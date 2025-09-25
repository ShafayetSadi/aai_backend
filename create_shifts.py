import asyncio
import sys
from datetime import time
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import get_session
from src.models.shift import Shift

async def create_standard_shifts(org_id: str):
    """Create standard shifts for an organization."""
    
    # Standard shifts to create
    standard_shifts = [
        {"name": "Morning", "start_time": time(8, 0), "end_time": time(16, 0)},
        {"name": "Afternoon", "start_time": time(12, 0), "end_time": time(20, 0)},
        {"name": "Evening", "start_time": time(16, 0), "end_time": time(24, 0)},
        {"name": "Night", "start_time": time(0, 0), "end_time": time(8, 0)},
    ]
    
    try:
        org_uuid = UUID(org_id)
    except ValueError:
        print(f"Invalid organization ID format: {org_id}")
        return
    
    async for session in get_session():
        for shift_data in standard_shifts:
            # Check if shift already exists
            from sqlalchemy import select
            existing = await session.execute(
                select(Shift).where(
                    Shift.organization_id == org_uuid,
                    Shift.name == shift_data["name"]
                )
            )
            
            if existing.scalar_one_or_none():
                print(f"Shift '{shift_data['name']}' already exists, skipping...")
                continue
            
            # Create new shift
            shift = Shift(
                organization_id=org_uuid,
                name=shift_data["name"],
                start_time=shift_data["start_time"],
                end_time=shift_data["end_time"]
            )
            
            session.add(shift)
            print(f"Created shift: {shift_data['name']} ({shift_data['start_time']} - {shift_data['end_time']})")
        
        await session.commit()
        print("All shifts created successfully!")
        break

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_shifts.py <organization_id>")
        sys.exit(1)
    
    org_id = sys.argv[1]
    asyncio.run(create_standard_shifts(org_id))
