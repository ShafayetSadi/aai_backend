"""
Schedule conflict detection service for workforce scheduling.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.core.logging import get_logger
from src.models.assignment import Assignment
from src.models.availability import Availability, AvailabilityStatus, TimeOffRequest
from src.models.schedule import RoleSlot, ScheduleDay
from src.models.shift import Shift
from src.models.role import Role
from src.models.base import RequestStatus

logger = get_logger(__name__)


class ConflictService:
    """Service for detecting scheduling conflicts."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def detect_conflicts(self, schedule_id: UUID) -> List[Dict[str, Any]]:
        """Detect all conflicts in a schedule."""

        conflicts = []

        # Check for overlapping assignments
        overlapping_conflicts = await self._find_overlapping_assignments(schedule_id)
        conflicts.extend(overlapping_conflicts)

        # Check for capacity violations
        capacity_conflicts = await self._find_capacity_violations(schedule_id)
        conflicts.extend(capacity_conflicts)

        # Check for availability violations
        availability_conflicts = await self._find_availability_violations(schedule_id)
        conflicts.extend(availability_conflicts)

        # Check for time off conflicts
        time_off_conflicts = await self._find_time_off_conflicts(schedule_id)
        conflicts.extend(time_off_conflicts)

        return conflicts

    async def _find_overlapping_assignments(
        self, schedule_id: UUID
    ) -> List[Dict[str, Any]]:
        """Find assignments that overlap in time."""

        conflicts = []

        # Get all assignments for this schedule
        assignments_result = await self.session.execute(
            select(Assignment)
            .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
            .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
            .where(ScheduleDay.schedule_id == schedule_id)
        )
        assignments = assignments_result.scalars().all()

        # Group assignments by user and date
        user_date_assignments = {}
        for assignment in assignments:
            # Get the schedule day
            day_result = await self.session.execute(
                select(ScheduleDay).where(ScheduleDay.id == assignment.role_slot_id)
            )
            day = day_result.scalar_one_or_none()

            if not day:
                continue

            key = (assignment.user_id, day.schedule_date)
            if key not in user_date_assignments:
                user_date_assignments[key] = []
            user_date_assignments[key].append(assignment)

        # Check for overlaps within each user-date group
        for (
            user_id,
            assignment_date,
        ), user_assignments in user_date_assignments.items():
            if len(user_assignments) < 2:
                continue

            # Get shift information for each assignment
            assignment_shifts = []
            for assignment in user_assignments:
                role_slot_result = await self.session.execute(
                    select(RoleSlot).where(RoleSlot.id == assignment.role_slot_id)
                )
                role_slot = role_slot_result.scalar_one_or_none()

                if not role_slot:
                    continue

                shift_result = await self.session.execute(
                    select(Shift).where(Shift.id == role_slot.shift_id)
                )
                shift = shift_result.scalar_one_or_none()

                if not shift:
                    continue

                assignment_shifts.append(
                    {"assignment": assignment, "role_slot": role_slot, "shift": shift}
                )

            # Check for time overlaps
            for i in range(len(assignment_shifts)):
                for j in range(i + 1, len(assignment_shifts)):
                    shift1 = assignment_shifts[i]["shift"]
                    shift2 = assignment_shifts[j]["shift"]

                    if self._shifts_overlap(shift1, shift2):
                        conflicts.append(
                            {
                                "type": "overlapping_assignments",
                                "severity": "high",
                                "user_id": user_id,
                                "date": assignment_date,
                                "conflict_details": {
                                    "assignment1_id": assignment_shifts[i][
                                        "assignment"
                                    ].id,
                                    "assignment2_id": assignment_shifts[j][
                                        "assignment"
                                    ].id,
                                    "shift1": f"{shift1.name} ({shift1.start_time}-{shift1.end_time})",
                                    "shift2": f"{shift2.name} ({shift2.start_time}-{shift2.end_time})",
                                },
                            }
                        )

        return conflicts

    async def _find_capacity_violations(
        self, schedule_id: UUID
    ) -> List[Dict[str, Any]]:
        """Find role slots that exceed their required capacity."""

        conflicts = []

        # Get all role slots for this schedule
        role_slots_result = await self.session.execute(
            select(RoleSlot)
            .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
            .where(ScheduleDay.schedule_id == schedule_id)
        )
        role_slots = role_slots_result.scalars().all()

        for role_slot in role_slots:
            # Count current assignments
            assigned_count_result = await self.session.execute(
                select(func.count(Assignment.id)).where(
                    Assignment.role_slot_id == role_slot.id
                )
            )
            assigned_count = assigned_count_result.scalar() or 0

            if assigned_count > role_slot.required_count:
                # Get role and day info
                role_result = await self.session.execute(
                    select(Role).where(Role.id == role_slot.role_id)
                )
                role = role_result.scalar_one_or_none()

                day_result = await self.session.execute(
                    select(ScheduleDay).where(
                        ScheduleDay.id == role_slot.schedule_day_id
                    )
                )
                day = day_result.scalar_one_or_none()

                if role and day:
                    conflicts.append(
                        {
                            "type": "capacity_violation",
                            "severity": "medium",
                            "role_slot_id": role_slot.id,
                            "role_name": role.name,
                            "date": day.schedule_date,
                            "conflict_details": {
                                "required": role_slot.required_count,
                                "assigned": assigned_count,
                                "excess": assigned_count - role_slot.required_count,
                            },
                        }
                    )

        return conflicts

    async def _find_availability_violations(
        self, schedule_id: UUID
    ) -> List[Dict[str, Any]]:
        """Find assignments that violate user availability."""

        conflicts = []

        # Get all assignments for this schedule
        assignments_result = await self.session.execute(
            select(Assignment)
            .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
            .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
            .where(ScheduleDay.schedule_id == schedule_id)
        )
        assignments = assignments_result.scalars().all()

        for assignment in assignments:
            # Get the schedule day
            day_result = await self.session.execute(
                select(ScheduleDay).where(ScheduleDay.id == assignment.role_slot_id)
            )
            day = day_result.scalar_one_or_none()

            if not day:
                continue

            # Get the role slot and shift
            role_slot_result = await self.session.execute(
                select(RoleSlot).where(RoleSlot.id == assignment.role_slot_id)
            )
            role_slot = role_slot_result.scalar_one_or_none()

            if not role_slot:
                continue

            # Check if user is marked as unavailable
            weekday = day.schedule_date.strftime("%A").lower()

            # Check recurring availability
            recurring_result = await self.session.execute(
                select(Availability).where(
                    Availability.user_id == assignment.user_id,
                    Availability.organization_id == assignment.organization_id,
                    Availability.shift_id == role_slot.shift_id,
                    Availability.availability_type == "Recurring",
                    Availability.availability_day == weekday,
                    Availability.status == AvailabilityStatus.Unavailable,
                )
            )
            if recurring_result.scalar_one_or_none():
                conflicts.append(
                    {
                        "type": "availability_violation",
                        "severity": "high",
                        "assignment_id": assignment.id,
                        "user_id": assignment.user_id,
                        "date": day.schedule_date,
                        "conflict_details": {
                            "reason": "User marked as unavailable for this recurring shift"
                        },
                    }
                )
                continue

            # Check exception availability
            exception_result = await self.session.execute(
                select(Availability).where(
                    Availability.user_id == assignment.user_id,
                    Availability.organization_id == assignment.organization_id,
                    Availability.shift_id == role_slot.shift_id,
                    Availability.availability_type == "Exception",
                    Availability.availability_date == day.schedule_date,
                    Availability.status == AvailabilityStatus.Unavailable,
                )
            )
            if exception_result.scalar_one_or_none():
                conflicts.append(
                    {
                        "type": "availability_violation",
                        "severity": "high",
                        "assignment_id": assignment.id,
                        "user_id": assignment.user_id,
                        "date": day.schedule_date,
                        "conflict_details": {
                            "reason": "User marked as unavailable for this specific date"
                        },
                    }
                )

        return conflicts

    async def _find_time_off_conflicts(self, schedule_id: UUID) -> List[Dict[str, Any]]:
        """Find assignments that conflict with approved time off requests."""

        conflicts = []

        # Get all assignments for this schedule
        assignments_result = await self.session.execute(
            select(Assignment)
            .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
            .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
            .where(ScheduleDay.schedule_id == schedule_id)
        )
        assignments = assignments_result.scalars().all()

        for assignment in assignments:
            # Get the schedule day
            day_result = await self.session.execute(
                select(ScheduleDay).where(ScheduleDay.id == assignment.role_slot_id)
            )
            day = day_result.scalar_one_or_none()

            if not day:
                continue

            # Check for time off requests
            time_off_result = await self.session.execute(
                select(TimeOffRequest).where(
                    TimeOffRequest.user_id == assignment.user_id,
                    TimeOffRequest.organization_id == assignment.organization_id,
                    TimeOffRequest.status == RequestStatus.Approved,
                    TimeOffRequest.start_dt
                    <= datetime.combine(day.schedule_date, time.max),
                    TimeOffRequest.end_dt
                    >= datetime.combine(day.schedule_date, time.min),
                )
            )
            time_off = time_off_result.scalar_one_or_none()

            if time_off:
                conflicts.append(
                    {
                        "type": "time_off_conflict",
                        "severity": "high",
                        "assignment_id": assignment.id,
                        "user_id": assignment.user_id,
                        "date": day.schedule_date,
                        "conflict_details": {
                            "time_off_request_id": time_off.id,
                            "time_off_period": f"{time_off.start_dt} - {time_off.end_dt}",
                            "reason": time_off.reason,
                        },
                    }
                )

        return conflicts

    def _shifts_overlap(self, shift1: Shift, shift2: Shift) -> bool:
        """Check if two shifts overlap in time."""
        return (
            shift1.start_time < shift2.end_time and shift2.start_time < shift1.end_time
        )
