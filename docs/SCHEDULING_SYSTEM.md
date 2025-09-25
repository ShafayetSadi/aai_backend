# Workforce Scheduling System

This document describes the comprehensive workforce scheduling system implemented for the AAI Backend.

## Overview

The scheduling system provides a flexible, organization-agnostic core for managing workforce schedules, covering roles, availability, requirement templates, and schedule management with auto-assignment capabilities.

## Architecture

### Core Components

1. **Domain Models** - SQLModel classes representing the scheduling entities
2. **Pydantic Schemas** - Request/response validation and serialization
3. **API Routers** - FastAPI endpoints for CRUD operations
4. **Service Layer** - Business logic and auto-assignment algorithms
5. **Database Migrations** - Alembic migrations for schema changes

### Key Features

- **Role Management**: Define roles within organizations
- **Availability Management**: Recurring patterns and one-off exceptions
- **Requirement Templates**: Reusable scheduling matrices for different week types
- **Schedule Management**: Draft → Published workflow with auto-assignment
- **Auto-Assignment Engine**: Intelligent staff assignment with fairness algorithms
- **Multi-View Support**: By-role and by-staff schedule views
- **Organization Scoping**: All operations are scoped to organizations

## Data Model

### Core Tables

1. **roles** - Organization roles for scheduling
2. **shift_templates** - Reusable shift patterns
3. **availability_recurring** - Weekly availability patterns
4. **availability_exceptions** - One-off availability overrides
5. **time_off_requests** - Staff time-off requests
6. **requirement_templates** - Reusable requirement matrices
7. **requirement_items** - Individual requirements within templates
8. **schedules** - Weekly schedules for organizations
9. **schedule_days** - Individual days within schedules
10. **shift_instances** - Specific shift instances on days
11. **role_slots** - Role requirements for shift instances
12. **assignments** - Staff assignments to role slots

### Relationships

- Organizations contain all scheduling entities
- Profiles have recurring availability and exceptions
- Requirement templates define weekly patterns
- Schedules are instantiated from templates
- Auto-assignment respects availability and constraints
- Schedule → ScheduleDay → ShiftInstance → RoleSlot → Assignment hierarchy

### Data Model Details

#### Schedule Hierarchy

```
Schedule (weekly schedule)
├── ScheduleDay (individual days)
    └── ShiftInstance (specific shifts on days)
        └── RoleSlot (role requirements for shifts)
            └── Assignment (staff assignments to role slots)
```

#### Availability System

- **AvailabilityRecurring**: Weekly patterns (e.g., "Available Monday 9-5")
- **AvailabilityException**: One-off overrides (e.g., "Unavailable Dec 25")
- **TimeOffRequest**: Staff requests with approval workflow

#### Requirement Templates

- **RequirementTemplate**: Named templates (e.g., "Busy Week", "Holiday Schedule")
- **RequirementItem**: Specific requirements per weekday/shift/role combination

#### Current Model Structure

The scheduling system uses a hierarchical approach:

1. **Organizations** contain all scheduling entities
2. **Roles** define job functions within organizations
3. **Profiles** represent staff members with availability
4. **Requirement Templates** define weekly staffing patterns
5. **Schedules** are instantiated from templates for specific weeks
6. **Assignments** link staff to specific role slots

All models inherit from `BaseModel` which provides:

- UUID primary keys
- Created/updated timestamps
- Soft delete functionality (`is_active` flag)
- Organization scoping

## API Endpoints

### Roles Management

- `POST /api/v1/organizations/{org_id}/roles` - Create role
- `GET /api/v1/organizations/{org_id}/roles` - List roles
- `GET /api/v1/organizations/{org_id}/roles/{role_id}` - Get role
- `PATCH /api/v1/organizations/{org_id}/roles/{role_id}` - Update role
- `DELETE /api/v1/organizations/{org_id}/roles/{role_id}` - Delete role

### Availability Management

- `GET /api/v1/organizations/{org_id}/profiles/{profile_id}/availability` - Get all availability
- `GET /api/v1/organizations/{org_id}/profiles/{profile_id}/availability/recurrences` - Get recurring availability
- `POST /api/v1/organizations/{org_id}/profiles/{profile_id}/availability/recurrences` - Create recurring
- `PATCH /api/v1/organizations/{org_id}/profiles/{profile_id}/availability/recurrences/{id}` - Update recurring
- `DELETE /api/v1/organizations/{org_id}/profiles/{profile_id}/availability/recurrences/{id}` - Delete recurring
- `GET /api/v1/organizations/{org_id}/profiles/{profile_id}/availability/exceptions` - Get exceptions
- `POST /api/v1/organizations/{org_id}/profiles/{profile_id}/availability/exceptions` - Create exception
- `PATCH /api/v1/organizations/{org_id}/profiles/{profile_id}/availability/exceptions/{id}` - Update exception
- `DELETE /api/v1/organizations/{org_id}/profiles/{profile_id}/availability/exceptions/{id}` - Delete exception

### Requirement Templates

- `POST /api/v1/organizations/{org_id}/requirement-templates` - Create template
- `GET /api/v1/organizations/{org_id}/requirement-templates` - List templates
- `GET /api/v1/organizations/{org_id}/requirement-templates/{id}` - Get template with items
- `PATCH /api/v1/organizations/{org_id}/requirement-templates/{id}` - Update template
- `DELETE /api/v1/organizations/{org_id}/requirement-templates/{id}` - Delete template
- `PUT /api/v1/organizations/{org_id}/requirement-templates/{id}/items` - Bulk update items
- `POST /api/v1/organizations/{org_id}/requirement-templates/{id}/instantiate-week` - Create schedule

### Schedule Management

- `POST /api/v1/organizations/{org_id}/schedules` - Create schedule
- `GET /api/v1/organizations/{org_id}/schedules` - List schedules
- `GET /api/v1/organizations/{org_id}/schedules/{id}` - Get schedule with days
- `PATCH /api/v1/organizations/{org_id}/schedules/{id}` - Update schedule
- `DELETE /api/v1/organizations/{org_id}/schedules/{id}` - Delete schedule
- `POST /api/v1/organizations/{org_id}/schedules/{id}/auto-assign` - Run auto-assignment
- `POST /api/v1/organizations/{org_id}/schedules/{id}/publish` - Publish schedule
- `GET /api/v1/organizations/{org_id}/schedules/{id}/by-role` - Role view
- `GET /api/v1/organizations/{org_id}/schedules/{id}/by-staff` - Staff view
- `GET /api/v1/organizations/{org_id}/profiles/{profile_id}/my-assignments` - My assignments

## Auto-Assignment Algorithm

### Scoring System

The auto-assignment engine uses a scoring system to rank candidates:

1. **Availability Score**:

   - Preferred: +2.0 points
   - Available: +1.0 points
   - Unavailable: 0 points (excluded)

2. **Fairness Bonus**:

   - Random component (0-0.1) for tie-breaking
   - Preference for less-assigned staff

3. **Hard Constraints**:
   - Time-off requests (approved) block assignment
   - Unavailable status blocks assignment

### Algorithm Steps

1. For each schedule slot, build candidate list
2. Filter candidates by availability and constraints
3. Score candidates based on availability and fairness
4. Sort by score (descending)
5. Assign top N candidates up to required_count
6. Track assignments for fairness calculations

### Fairness Metrics

- **Fairness Index**: Standard deviation of assignments per staff member
- **Fill Rate**: Percentage of slots successfully filled
- **Shortfall Tracking**: Detailed reporting of unfilled slots

## Usage Examples

### 1. Create a Role

```python
POST /api/v1/organizations/{org_id}/roles
{
    "name": "Barista",
    "slug": "barista",
    "description": "Coffee shop barista"
}
```

### 2. Set Staff Availability

```python
POST /api/v1/organizations/{org_id}/profiles/{profile_id}/availability/recurrences
{
    "organization_id": "org-uuid",
    "profile_id": "profile-uuid",
    "weekday": 0,  # Monday
    "start_time": "09:00",
    "end_time": "17:00",
    "status": "preferred"
}
```

### 3. Create Requirement Template

```python
POST /api/v1/organizations/{org_id}/requirement-templates
{
    "organization_id": "org-uuid",
    "name": "Busy Week",
    "notes": "High-traffic week requirements"
}
```

### 4. Add Requirement Items

```python
PUT /api/v1/organizations/{org_id}/requirement-templates/{id}/items
{
    "items": [
        {
            "organization_id": "org-uuid",
            "requirement_template_id": "template-uuid",
            "weekday": 0,
            "shift_template_id": "shift-uuid",
            "role_id": "barista-role-uuid",
            "required_count": 3
        }
    ]
}
```

### 5. Instantiate Schedule

```python
POST /api/v1/organizations/{org_id}/requirement-templates/{id}/instantiate-week
{
    "week_start": "2024-01-01"
}
```

### 6. Run Auto-Assignment

```python
POST /api/v1/organizations/{org_id}/schedules/{id}/auto-assign
```

### 7. Publish Schedule

```python
POST /api/v1/organizations/{org_id}/schedules/{id}/publish
```

## Security & Permissions

- All endpoints require authentication
- Organization scoping enforced at query level
- Manager/Admin roles required for write operations
- Staff can only view their own assignments
- Cross-organization data leakage prevented

## Performance Considerations

- Indexed queries for organization scoping
- Efficient candidate filtering
- Batch operations for bulk updates
- Structured logging for observability
- Configurable pagination limits

## Future Enhancements

- **Shift Swaps**: Allow staff to swap shifts
- **Skill Management**: Add skills system with proficiency levels
- **Demand Forecasting**: Integrate with POS/appointment data
- **Background Jobs**: Automated weekly schedule generation
- **Advanced Constraints**: More sophisticated assignment rules
- **Mobile Support**: Staff mobile app for availability management
- **Time Off Management**: Complete time-off request workflow
- **Schedule Templates**: Pre-built schedule templates for common patterns
- **Conflict Resolution**: Automated conflict detection and resolution
- **Performance Analytics**: Detailed scheduling performance metrics

## Current Implementation Status

### ✅ Implemented Features

- **Core Models**: All scheduling models with proper relationships
- **Role Management**: Full CRUD operations for roles
- **Availability Management**: Recurring patterns and exceptions
- **Requirement Templates**: Template creation and management
- **Schedule Management**: Basic schedule CRUD operations
- **Auto-Assignment Engine**: Intelligent staff assignment algorithm
- **API Endpoints**: Complete REST API for all operations
- **Authentication**: JWT-based authentication and authorization
- **Organization Scoping**: All operations properly scoped to organizations

### 🚧 Partially Implemented

- **Time Off Requests**: Models exist but workflow incomplete
- **Schedule Views**: Basic by-role and by-staff views implemented

### ❌ Not Yet Implemented

- **Skills System**: No skills management yet
- **Shift Swaps**: Staff cannot swap shifts
- **Advanced Constraints**: Basic constraints only
- **Background Jobs**: No automated scheduling
- **Mobile Support**: No mobile-specific endpoints

## Database Migration

To apply the scheduling system to your database:

```bash
# Run the migration
alembic upgrade head
```

This will create all the necessary tables and indexes for the scheduling system.

## Testing

The system includes comprehensive test coverage for:

- Model validation
- API endpoint functionality
- Auto-assignment algorithms
- Permission enforcement
- Edge cases and error handling

Run tests with:

```bash
pytest tests/scheduling/
```

## Monitoring

The system provides structured logging for:

- Schedule instantiation metrics
- Auto-assignment decisions
- Shortfall tracking
- Performance monitoring
- Error tracking

Key metrics to monitor:

- `scheduling.assignments_made`
- `scheduling.shortfalls_total`
- `scheduling.fairness_index`
- `scheduling.fill_rate`
