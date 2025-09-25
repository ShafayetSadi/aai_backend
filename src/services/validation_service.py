"""
Business validation service for workforce scheduling.
"""

from __future__ import annotations

from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from src.core.logging import get_logger
from src.models.assignment import Assignment, AssignmentStatus
from src.models.availability import Availability, AvailabilityStatus, TimeOffRequest
from src.models.schedule import RoleSlot, ScheduleDay
from src.models.shift import Shift
from src.models.user import User
from src.models.base import RequestStatus

logger = get_logger(__name__)


class ValidationService:
    """Service for validating business rules and constraints."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate_assignment_constraints(
        self, user_id: UUID, role_slot_id: UUID, org_id: UUID, assignment_date: date
    ) -> Dict[str, Any]:
        """Validate assignment constraints for a user and role slot."""

        validation_result = {"is_valid": True, "violations": [], "warnings": []}

        # Check 1: Maximum assignments per week
        week_start = self._get_week_start(assignment_date)
        week_end = self._get_week_end(assignment_date)

        current_assignments = await self._count_user_assignments_this_week(
            user_id, org_id, week_start, week_end
        )

        max_assignments = 5  # Business rule
        if current_assignments >= max_assignments:
            validation_result["is_valid"] = False
            validation_result["violations"].append(
                f"User has {current_assignments}/{max_assignments} assignments this week"
            )

        # Check 2: Time off conflicts
        has_time_off = await self._check_time_off_conflict(
            user_id, org_id, assignment_date
        )
        if has_time_off:
            validation_result["is_valid"] = False
            validation_result["violations"].append(
                "User has approved time off on this date"
            )

        # Check 3: Availability conflicts
        availability_conflict = await self._check_availability_conflict(
            user_id, org_id, assignment_date, role_slot_id
        )
        if availability_conflict:
            validation_result["is_valid"] = False
            validation_result["violations"].append(
                "User is marked as unavailable for this shift"
            )

        # Check 4: Double booking (same time slot)
        double_booking = await self._check_double_booking(
            user_id, org_id, assignment_date, role_slot_id
        )
        if double_booking:
            validation_result["is_valid"] = False
            validation_result["violations"].append(
                "User is already assigned to another shift at the same time"
            )

        # Check 5: Role capacity
        role_capacity_exceeded = await self._check_role_capacity(role_slot_id, org_id)
        if role_capacity_exceeded:
            validation_result["warnings"].append("Role slot is at or near capacity")

        return validation_result

    async def validate_schedule_constraints(self, schedule_id: UUID) -> Dict[str, Any]:
        """Validate overall schedule constraints."""

        validation_result = {
            "is_valid": True,
            "violations": [],
            "warnings": [],
            "statistics": {},
        }

        # Get all role slots for this schedule
        role_slots_result = await self.session.execute(
            select(RoleSlot)
            .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
            .where(ScheduleDay.schedule_id == schedule_id)
        )
        role_slots = role_slots_result.scalars().all()

        total_slots = len(role_slots)
        filled_slots = 0
        over_assigned_slots = 0
        under_assigned_slots = 0

        for role_slot in role_slots:
            # Count current assignments
            assigned_count_result = await self.session.execute(
                select(func.count(Assignment.id)).where(
                    Assignment.role_slot_id == role_slot.id
                )
            )
            assigned_count = assigned_count_result.scalar() or 0

            if assigned_count > 0:
                filled_slots += 1

            if assigned_count > role_slot.required_count:
                over_assigned_slots += 1
                validation_result["warnings"].append(
                    f"Role slot {role_slot.id} is over-assigned: {assigned_count}/{role_slot.required_count}"
                )

            if assigned_count < role_slot.required_count:
                under_assigned_slots += 1

        # Calculate statistics
        fill_rate = (filled_slots / total_slots * 100) if total_slots > 0 else 0
        validation_result["statistics"] = {
            "total_slots": total_slots,
            "filled_slots": filled_slots,
            "fill_rate": fill_rate,
            "over_assigned_slots": over_assigned_slots,
            "under_assigned_slots": under_assigned_slots,
        }

        # Check for critical issues
        if fill_rate < 50:  # Less than 50% fill rate
            validation_result["warnings"].append(
                f"Schedule has low fill rate: {fill_rate:.1f}%"
            )

        return validation_result

    async def _count_user_assignments_this_week(
        self, user_id: UUID, org_id: UUID, week_start: date, week_end: date
    ) -> int:
        """Count user assignments in a specific week."""

        result = await self.session.execute(
            select(func.count(Assignment.id))
            .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
            .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
            .where(
                Assignment.user_id == user_id,
                Assignment.organization_id == org_id,
                ScheduleDay.schedule_date >= week_start,
                ScheduleDay.schedule_date <= week_end,
            )
        )
        return result.scalar() or 0

    async def _check_time_off_conflict(
        self, user_id: UUID, org_id: UUID, assignment_date: date
    ) -> bool:
        """Check if user has time off on the assignment date."""

        result = await self.session.execute(
            select(TimeOffRequest).where(
                TimeOffRequest.user_id == user_id,
                TimeOffRequest.organization_id == org_id,
                TimeOffRequest.status == RequestStatus.Approved,
                TimeOffRequest.start_dt <= datetime.combine(assignment_date, time.max),
                TimeOffRequest.end_dt >= datetime.combine(assignment_date, time.min),
            )
        )
        return result.scalar_one_or_none() is not None

    async def _check_availability_conflict(
        self, user_id: UUID, org_id: UUID, assignment_date: date, role_slot_id: UUID
    ) -> bool:
        """Check if user is unavailable for this specific shift."""

        # Get the role slot and its shift
        role_slot_result = await self.session.execute(
            select(RoleSlot).where(RoleSlot.id == role_slot_id)
        )
        role_slot = role_slot_result.scalar_one_or_none()

        if not role_slot:
            return True  # Invalid role slot

        # Check recurring availability
        weekday = assignment_date.strftime("%A").lower()
        recurring_result = await self.session.execute(
            select(Availability).where(
                Availability.user_id == user_id,
                Availability.organization_id == org_id,
                Availability.shift_id == role_slot.shift_id,
                Availability.availability_type == "Recurring",
                Availability.availability_day == weekday,
                Availability.status == AvailabilityStatus.Unavailable,
            )
        )
        if recurring_result.scalar_one_or_none():
            return True

        # Check exception availability
        exception_result = await self.session.execute(
            select(Availability).where(
                Availability.user_id == user_id,
                Availability.organization_id == org_id,
                Availability.shift_id == role_slot.shift_id,
                Availability.availability_type == "Exception",
                Availability.availability_date == assignment_date,
                Availability.status == AvailabilityStatus.Unavailable,
            )
        )
        return exception_result.scalar_one_or_none() is not None

    async def _check_double_booking(
        self, user_id: UUID, org_id: UUID, assignment_date: date, role_slot_id: UUID
    ) -> bool:
        """Check if user is already assigned to another shift at the same time."""

        # Get the role slot and its shift
        role_slot_result = await self.session.execute(
            select(RoleSlot).where(RoleSlot.id == role_slot_id)
        )
        role_slot = role_slot_result.scalar_one_or_none()

        if not role_slot:
            return True  # Invalid role slot

        # Get the shift for this role slot
        shift_result = await self.session.execute(
            select(Shift).where(Shift.id == role_slot.shift_id)
        )
        shift = shift_result.scalar_one_or_none()

        if not shift:
            return True  # Invalid shift

        # Check for overlapping assignments on the same date
        overlapping_result = await self.session.execute(
            select(Assignment)
            .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
            .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
            .join(Shift, RoleSlot.shift_id == Shift.id)
            .where(
                Assignment.user_id == user_id,
                Assignment.organization_id == org_id,
                ScheduleDay.schedule_date == assignment_date,
                or_(
                    and_(
                        Shift.start_time < shift.end_time,
                        Shift.end_time > shift.start_time,
                    )
                ),
            )
        )
        return overlapping_result.scalar_one_or_none() is not None

    async def _check_role_capacity(self, role_slot_id: UUID, org_id: UUID) -> bool:
        """Check if role slot is at or near capacity."""

        # Get the role slot
        role_slot_result = await self.session.execute(
            select(RoleSlot).where(RoleSlot.id == role_slot_id)
        )
        role_slot = role_slot_result.scalar_one_or_none()

        if not role_slot:
            return True  # Invalid role slot

        # Count current assignments
        assigned_count_result = await self.session.execute(
            select(func.count(Assignment.id)).where(
                Assignment.role_slot_id == role_slot_id
            )
        )
        assigned_count = assigned_count_result.scalar() or 0

        # Check if at or near capacity (90% threshold)
        capacity_threshold = role_slot.required_count * 0.9
        return assigned_count >= capacity_threshold

    def _get_week_start(self, date_obj: date) -> date:
        """Get the start of the week (Monday) for a given date."""
        days_since_monday = date_obj.weekday()
        return date_obj - timedelta(days=days_since_monday)

    def _get_week_end(self, date_obj: date) -> date:
        """Get the end of the week (Sunday) for a given date."""
        days_until_sunday = 6 - date_obj.weekday()
        return date_obj + timedelta(days=days_until_sunday)
