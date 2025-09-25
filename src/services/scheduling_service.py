"""
Scheduling service for workforce management.
"""

from __future__ import annotations

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from uuid import UUID
import random
import statistics

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.core.logging import get_logger
from src.models.schedule import (
    Schedule,
    ScheduleStatus,
    ScheduleDay,
    RoleSlot,
    Assignment,
)
from src.models.role import Role
from src.models.shift import Shift
from src.models.user import User
from src.models.availability import Availability, AvailabilityStatus, TimeOffRequest
from src.models.base import Weekday, RequestStatus
from src.schemas.schedule import (
    AutoAssignResult,
    ScheduleByRoleView,
    ScheduleByStaffView,
)

logger = get_logger(__name__)


class SchedulingService:
    """Service for managing workforce scheduling operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def auto_assign(
        self,
        schedule_id: UUID,
        policy: Optional[Dict[str, Any]] = None,
    ) -> AutoAssignResult:
        """Run auto-assignment for a schedule."""

        logger.info("Starting auto-assignment", schedule_id=str(schedule_id))

        # Get schedule
        schedule_result = await self.session.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = schedule_result.scalar_one_or_none()

        if not schedule:
            raise ValueError("Schedule not found")

        # Get all role slots for the schedule
        role_slots_result = await self.session.execute(
            select(RoleSlot)
            .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
            .where(ScheduleDay.schedule_id == schedule_id)
        )
        role_slots = role_slots_result.scalars().all()

        # Get all active users in the organization
        users_result = await self.session.execute(select(User).where(User.is_active))
        users = users_result.scalars().all()

        # Build candidate lists for each slot
        assignments_made = 0
        total_slots = len(role_slots)
        filled_slots = 0

        for role_slot in role_slots:
            # Get the schedule day for this role slot
            day_result = await self.session.execute(
                select(ScheduleDay).where(ScheduleDay.id == role_slot.schedule_day_id)
            )
            day = day_result.scalar_one_or_none()

            if not day:
                continue

            # Get the shift for this role slot to get start/end times
            shift_result = await self.session.execute(
                select(Shift).where(Shift.id == role_slot.shift_id)
            )
            shift = shift_result.scalar_one_or_none()

            if not shift:
                continue

            candidates = await self._get_candidates_for_window(
                date=day.schedule_date,
                start_time=shift.start_time,
                end_time=shift.end_time,
                users=users,
                org_id=schedule.organization_id,
            )

            # Sort candidates by score
            candidates.sort(key=lambda x: x["score"], reverse=True)

            # Assign top candidates up to required_count
            assigned_count = 0
            for candidate in candidates:
                if assigned_count >= role_slot.required_count:
                    break

                # Create assignment
                assignment = Assignment(
                    organization_id=schedule.organization_id,
                    role_slot_id=role_slot.id,
                    user_id=candidate["user_id"],
                    assigned_at=datetime.utcnow(),
                )
                self.session.add(assignment)
                assignments_made += 1
                assigned_count += 1

            if assigned_count > 0:
                filled_slots += 1

        await self.session.commit()

        # Calculate metrics
        fill_rate = (filled_slots / total_slots) * 100 if total_slots > 0 else 0
        shortfalls = await self.compute_open_demand(schedule_id)
        fairness_index = await self._calculate_fairness_index(schedule_id)

        logger.info(
            "Auto-assignment completed",
            schedule_id=str(schedule_id),
            total_slots=total_slots,
            filled_slots=filled_slots,
            fill_rate=fill_rate,
            assignments_made=assignments_made,
        )

        return AutoAssignResult(
            schedule_id=schedule_id,
            total_slots=total_slots,
            filled_slots=filled_slots,
            fill_rate=fill_rate,
            assignments_made=assignments_made,
            shortfalls=shortfalls,
            fairness_index=fairness_index,
        )

    async def _get_candidates_for_window(
        self,
        date: date,
        start_time: Optional[time],
        end_time: Optional[time],
        users: List[User],
        org_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get and score candidates for a specific time window."""

        candidates = []
        slot_weekday = date.weekday()

        for user in users:
            # Check availability
            is_available = await self._check_availability(
                user.id,
                slot_weekday,
                date,
                start_time,
                end_time,
                org_id,
            )

            if not is_available:
                continue

            # Calculate score
            score = await self._calculate_candidate_score(user, date, org_id)

            candidates.append(
                {
                    "user_id": user.id,
                    "score": score,
                }
            )

        return candidates

    async def _check_availability(
        self,
        user_id: UUID,
        weekday: int,
        date: date,
        start_time: Optional[time],
        end_time: Optional[time],
        org_id: UUID,
    ) -> bool:
        """Check if a user is available for a specific time slot."""

        # Check time off requests first
        time_off_result = await self.session.execute(
            select(TimeOffRequest).where(
                TimeOffRequest.user_id == user_id,
                TimeOffRequest.organization_id == org_id,
                TimeOffRequest.status == RequestStatus.Approved,
                TimeOffRequest.start_dt <= datetime.combine(date, end_time or time.max),
                TimeOffRequest.end_dt >= datetime.combine(date, start_time or time.min),
            )
        )
        if time_off_result.scalar_one_or_none():
            return False

        weekday_enum = Weekday(date.strftime("%A").lower())

        # Check availability (unified model)
        availability_result = await self.session.execute(
            select(Availability).where(
                Availability.user_id == user_id,
                Availability.organization_id == org_id,
                Availability.availability_type == "Recurring",
                Availability.availability_day == weekday_enum,
            )
        )
        recurring = availability_result.scalar_one_or_none()

        if recurring:
            if recurring.status == AvailabilityStatus.Unavailable:
                return False
            elif recurring.status in [
                AvailabilityStatus.Available,
                AvailabilityStatus.Off,
            ]:
                return True

        # Check exception availability for this specific date
        exception_result = await self.session.execute(
            select(Availability).where(
                Availability.user_id == user_id,
                Availability.organization_id == org_id,
                Availability.availability_type == "Exception",
                Availability.availability_date == date,
            )
        )
        exception = exception_result.scalar_one_or_none()

        if exception:
            if exception.status == AvailabilityStatus.Unavailable:
                return False
            elif exception.status in [
                AvailabilityStatus.Available,
                AvailabilityStatus.Off,
            ]:
                return True

        # Default to available if no specific rules
        return True

    async def _calculate_candidate_score(
        self,
        user: User,
        date: date,
        org_id: UUID,
    ) -> float:
        """Calculate a score for a candidate user for a specific slot."""

        score = 0.0

        # Base availability score
        slot_weekday = Weekday(date.strftime("%A").lower())

        # Check recurring availability
        recurring_result = await self.session.execute(
            select(Availability).where(
                Availability.user_id == user.id,
                Availability.organization_id == org_id,
                Availability.availability_type == "Recurring",
                Availability.availability_day == slot_weekday,
            )
        )
        recurring = recurring_result.scalar_one_or_none()

        if recurring:
            if recurring.status == AvailabilityStatus.Available:
                score += 2.0
            elif recurring.status == AvailabilityStatus.Off:
                score += 1.0

        # Check exceptions
        exception_result = await self.session.execute(
            select(Availability).where(
                Availability.user_id == user.id,
                Availability.organization_id == org_id,
                Availability.availability_type == "Exception",
                Availability.availability_date == date,
            )
        )
        exception = exception_result.scalar_one_or_none()

        if exception:
            if exception.status == AvailabilityStatus.Available:
                score += 2.0
            elif exception.status == AvailabilityStatus.Off:
                score += 1.0

        # Add some randomness for fairness
        score += random.uniform(0, 0.1)

        return score

    async def _calculate_fairness_index(self, schedule_id: UUID) -> float:
        """Calculate fairness index based on assignment distribution."""

        # Get all assignments for this schedule by traversing through role slots
        assignments_result = await self.session.execute(
            select(Assignment)
            .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
            .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
            .where(ScheduleDay.schedule_id == schedule_id)
        )
        assignments = assignments_result.scalars().all()

        # Count assignments per user
        user_counts = {}
        for assignment in assignments:
            user_id = assignment.user_id
            user_counts[user_id] = user_counts.get(user_id, 0) + 1

        if not user_counts:
            return 0.0

        # Calculate standard deviation
        counts = list(user_counts.values())
        if len(counts) <= 1:
            return 0.0

        mean_count = statistics.mean(counts)
        variance = statistics.variance(counts, mean_count)
        std_dev = variance**0.5

        # Normalize to 0-1 scale (lower is better)
        fairness_index = max(0, 1 - (std_dev / mean_count)) if mean_count > 0 else 0

        return fairness_index

    async def publish_schedule(self, schedule_id: UUID) -> Schedule:
        """Publish a schedule."""

        logger.info("Publishing schedule", schedule_id=str(schedule_id))

        # Get schedule
        schedule_result = await self.session.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        schedule = schedule_result.scalar_one_or_none()

        if not schedule:
            raise ValueError("Schedule not found")

        # Check for shortfalls
        shortfalls = await self.compute_open_demand(schedule_id)
        if shortfalls:
            logger.warning(
                "Publishing schedule with shortfalls",
                schedule_id=str(schedule_id),
                shortfall_count=len(shortfalls),
            )

        # Update status
        schedule.status = ScheduleStatus.Published
        await self.session.commit()

        logger.info("Schedule published successfully", schedule_id=str(schedule_id))

        return schedule

    async def get_schedule_by_role(self, schedule_id: UUID) -> List[ScheduleByRoleView]:
        """Get schedule view organized by role."""

        # Get all role slots for this schedule
        role_slots_result = await self.session.execute(
            select(RoleSlot)
            .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
            .where(ScheduleDay.schedule_id == schedule_id)
        )
        role_slots = role_slots_result.scalars().all()

        # Build by-role view
        by_role_views = []
        for role_slot in role_slots:
            # Get related data
            day_result = await self.session.execute(
                select(ScheduleDay).where(ScheduleDay.id == role_slot.schedule_day_id)
            )
            day = day_result.scalar_one_or_none()

            role_result = await self.session.execute(
                select(Role).where(Role.id == role_slot.role_id)
            )
            role = role_result.scalar_one_or_none()

            shift_result = await self.session.execute(
                select(Shift).where(Shift.id == role_slot.shift_id)
            )
            shift = shift_result.scalar_one_or_none()

            if not all([day, role, shift]):
                continue

            assigned_count = (
                await self.session.execute(
                    select(func.count(Assignment.id)).where(
                        Assignment.role_slot_id == role_slot.id
                    )
                )
            ).scalar() or 0
            shortfall = max(0, role_slot.required_count - int(assigned_count))

            by_role_views.append(
                ScheduleByRoleView(
                    role_name=role.name,
                    day=day.schedule_date.strftime("%A"),
                    date=day.schedule_date,
                    shift=f"{shift.start_time} - {shift.end_time}",
                    assigned=int(assigned_count),
                    shortfall=shortfall,
                )
            )

        return by_role_views

    async def get_schedule_by_staff(
        self, schedule_id: UUID
    ) -> List[ScheduleByStaffView]:
        """Get schedule view organized by staff."""

        # Get assignments with users and roles
        assignments_result = await self.session.execute(
            select(Assignment)
            .join(RoleSlot, Assignment.role_slot_id == RoleSlot.id)
            .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
            .where(ScheduleDay.schedule_id == schedule_id)
        )
        assignments = assignments_result.scalars().all()

        # Build by-staff view
        by_staff_views = []
        for assignment in assignments:
            role_slot_result = await self.session.execute(
                select(RoleSlot).where(RoleSlot.id == assignment.role_slot_id)
            )
            role_slot = role_slot_result.scalar_one_or_none()

            if not role_slot:
                continue

            role_result = await self.session.execute(
                select(Role).where(Role.id == role_slot.role_id)
            )
            role = role_result.scalar_one_or_none()

            day_result = await self.session.execute(
                select(ScheduleDay).where(ScheduleDay.id == role_slot.schedule_day_id)
            )
            day = day_result.scalar_one_or_none()

            user_result = await self.session.execute(
                select(User).where(User.id == assignment.user_id)
            )
            user = user_result.scalar_one_or_none()

            if not all([role, day, user]):
                continue

            # Get shift for this role slot
            shift_result = await self.session.execute(
                select(Shift).where(Shift.id == role_slot.shift_id)
            )
            shift = shift_result.scalar_one_or_none()

            if not shift:
                continue

            by_staff_views.append(
                ScheduleByStaffView(
                    staff_name=user.username or "Unknown",
                    role_name=role.name,
                    day=day.schedule_date.strftime("%A"),
                    date=day.schedule_date,
                    shift=f"{shift.start_time} - {shift.end_time}",
                )
            )

        return by_staff_views

    async def _compute_open_demand(self, schedule_id: UUID) -> List[Dict[str, Any]]:
        """Compute open demand (unfilled role slots) for a schedule."""
        shortfalls = []

        # Get all role slots for this schedule
        role_slots_result = await self.session.execute(
            select(RoleSlot)
            .join(ScheduleDay, RoleSlot.schedule_day_id == ScheduleDay.id)
            .where(ScheduleDay.schedule_id == schedule_id)
        )
        role_slots = role_slots_result.scalars().all()

        for role_slot in role_slots:
            # Count current assignments for this role slot
            assigned_count_result = await self.session.execute(
                select(func.count(Assignment.id)).where(
                    Assignment.role_slot_id == role_slot.id
                )
            )
            assigned_count = assigned_count_result.scalar() or 0

            # Calculate shortfall
            shortfall = max(0, role_slot.required_count - assigned_count)

            if shortfall > 0:
                # Get role and day info for context
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

                # Get shift for this role slot
                shift_result = await self.session.execute(
                    select(Shift).where(Shift.id == role_slot.shift_id)
                )
                shift = shift_result.scalar_one_or_none()

                if role and day and shift:
                    shortfalls.append(
                        {
                            "role_name": role.name,
                            "date": day.schedule_date,
                            "required": role_slot.required_count,
                            "assigned": assigned_count,
                            "shortfall": shortfall,
                            "start_time": shift.start_time,
                            "end_time": shift.end_time,
                        }
                    )

        return shortfalls
