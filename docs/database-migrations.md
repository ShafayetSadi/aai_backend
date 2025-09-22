# Database Migration Guide

This guide provides comprehensive instructions for managing database migrations in the AAI Backend project using Alembic with SQLModel/SQLAlchemy.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Migration Workflow](#migration-workflow)
- [Common Commands](#common-commands)
- [Production Migration](#production-migration)
- [Rollback Procedures](#rollback-procedures)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## 🔧 Prerequisites

### Environment Setup

```bash
# Activate your virtual environment
source .venv/bin/activate

# Ensure you're in the project root
cd /home/shafayetsadi/aai/aai_backend
```

### Verify Alembic Configuration

```bash
# Check if Alembic is properly configured
alembic --version

# Verify current migration status
alembic current
```

## 🚀 Migration Workflow

### 1. Check Current Status

Before making any changes, always check the current state:

```bash
# Check current migration status
alembic current

# Check migration history
alembic history --verbose

# Check if there are any pending migrations
alembic show head
```

### 2. After Making Model Changes

#### Step 2.1: Generate Migration

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "Description of your changes"

# Examples:
alembic revision --autogenerate -m "Add user profile fields"
alembic revision --autogenerate -m "Update user table structure"
alembic revision --autogenerate -m "Add indexes to profile table"
alembic revision --autogenerate -m "Fix BaseModel table inheritance"
```

#### Step 2.2: Review Generated Migration

```bash
# List all migration files
ls -la alembic/versions/

# Review the latest migration file
cat alembic/versions/[latest_migration_file].py
```

**⚠️ Important:** Always review the generated migration before applying it!

#### Step 2.3: Apply Migration (Development)

```bash
# Apply the migration to your development database
alembic upgrade head
```

#### Step 2.4: Verify Migration

```bash
# Check current status after migration
alembic current

# Verify the migration was applied
alembic history --verbose

# Test that the application still works
python -c "from src.main import app; print('Application loaded successfully!')"
```

## 📝 Common Commands

### Basic Migration Commands

```bash
# Create empty migration (for manual changes)
alembic revision -m "Manual migration description"

# Show current revision
alembic current

# Show migration history
alembic history

# Show specific revision details
alembic show <revision_id>

# Check for pending migrations
alembic check

# Stamp database to specific revision (without running migration)
alembic stamp <revision_id>
```

### Advanced Commands

```bash
# Merge multiple heads (if you have branching)
alembic merge -m "Merge heads" <revision1> <revision2>

# Show SQL that would be executed (without running)
alembic upgrade head --sql

# Show specific revision SQL
alembic show <revision_id> --sql
```

## 🏭 Production Migration

### Pre-Migration Checklist

1. **Backup Database** (CRITICAL)
2. **Test on Staging Environment**
3. **Plan Downtime** (if needed)
4. **Notify Team** of migration schedule

### Step-by-Step Production Migration

#### Step 1: Backup Database

```bash
# For PostgreSQL
pg_dump -h localhost -U username -d database_name > backup_$(date +%Y%m%d_%H%M%S).sql

# For SQLite
cp database.db database_backup_$(date +%Y%m%d_%H%M%S).db

# Verify backup
ls -la backup_*.sql
```

#### Step 2: Test on Staging

```bash
# Apply to staging environment first
alembic upgrade head

# Run tests
pytest tests/

# Verify application functionality
```

#### Step 3: Apply to Production

```bash
# Apply to production
alembic upgrade head

# Verify migration success
alembic current
```

## 🔄 Rollback Procedures

### Check Available Revisions

```bash
# See all available revisions
alembic history --verbose

# Check current revision
alembic current
```

### Rollback Commands

```bash
# Rollback to previous revision
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback to base (empty database)
alembic downgrade base

# Rollback multiple steps
alembic downgrade -2  # Go back 2 revisions
```

### Post-Rollback Verification

```bash
# Check current state
alembic current

# Test application
python -c "from src.main import app; print('Rollback successful!')"
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Migration Conflicts

```bash
# Check for multiple heads
alembic heads

# If you have multiple heads, merge them
alembic merge -m "Merge heads" <head1> <head2>
```

#### 2. Failed Migration

```bash
# Check current state
alembic current

# Check what went wrong
alembic show <failed_revision_id>

# Fix the issue and create new migration
alembic revision --autogenerate -m "Fix failed migration"
```

#### 3. Database Connection Issues

```bash
# Check database connection
python -c "from src.core.db import check_db_connection; import asyncio; print(asyncio.run(check_db_connection()))"

# Verify environment variables
echo $DATABASE_URL
```

#### 4. Reset Migration History (Development Only)

```bash
# WARNING: This will lose all migration history
# Only use in development

# 1. Drop all tables manually or via database client
# 2. Delete all migration files
rm alembic/versions/*.py

# 3. Create new initial migration
alembic revision --autogenerate -m "Initial migration"

# 4. Apply migration
alembic upgrade head
```

### Debugging Tips

```bash
# Enable verbose logging
alembic -x verbose=true upgrade head

# Check what SQL would be executed
alembic upgrade head --sql

# Test migration without applying
alembic upgrade head --sql | head -20
```

## ✅ Best Practices

### 1. Always Review Generated Migrations

```bash
# Before applying, check what will be changed
alembic upgrade head --sql
```

### 2. Test Migrations Thoroughly

- Test on a copy of production data
- Verify data integrity after migration
- Test rollback procedures

### 3. Handle Data Migrations

```python
# In migration file, add data migration if needed
def upgrade():
    # ... schema changes ...

    # Data migration
    connection = op.get_bind()
    connection.execute(
        "UPDATE users SET is_active = true WHERE is_active IS NULL"
    )
```

### 4. Use Descriptive Migration Messages

```bash
# Good examples
alembic revision --autogenerate -m "Add user profile table with foreign key to users"
alembic revision --autogenerate -m "Add indexes to improve query performance"
alembic revision --autogenerate -m "Rename user_id to profile_user_id in profiles table"
alembic revision --autogenerate -m "Add relationships to profile models"
alembic revision --autogenerate -m "Add contacts and jobs tables with foreign keys to profiles"
alembic revision --autogenerate -m "Fix circular dependency in profile relationships"

# Bad examples
alembic revision --autogenerate -m "Update table"
alembic revision --autogenerate -m "Fix"
alembic revision --autogenerate -m "Changes"
```

### 5. Version Control

- Always commit migration files to version control
- Never edit existing migration files after they've been applied to production
- Create new migrations for fixes

### 6. Backup Strategy

- Always backup before major migrations
- Test restore procedures regularly
- Keep multiple backup versions

## 📊 Migration Examples

### Example 1: Adding a New Table

```bash
# 1. Add new model to models/
# 2. Generate migration
alembic revision --autogenerate -m "Add organizations table"

# 3. Review generated file
cat alembic/versions/[newest_file].py

# 4. Apply migration
alembic upgrade head
```

### Example 2: Adding a Column

```bash
# 1. Add column to existing model
# 2. Generate migration
alembic revision --autogenerate -m "Add email_verified column to users table"

# 3. Apply migration
alembic upgrade head
```

### Example 3: Adding an Index

```bash
# 1. Add index to model field
# 2. Generate migration
alembic revision --autogenerate -m "Add index to user email field"

# 3. Apply migration
alembic upgrade head
```

### Example 4: Adding Relationships

```bash
# 1. Add relationship fields to models
# Example: Adding location relationship to Profile model
# In src/models/profile.py:
# location: Optional[Location] = Relationship(back_populates="profiles")

# 2. Generate migration
alembic revision --autogenerate -m "Add relationships to profile models"

# 3. Review the generated migration
cat alembic/versions/[latest_file].py

# 4. Apply migration
alembic upgrade head
```

### Example 5: Adding New Related Tables

```bash
# 1. Create new models with relationships
# Example: Adding Contact and Job models to profile.py

# 2. Generate migration
alembic revision --autogenerate -m "Add contacts and jobs tables with relationships"

# 3. Review generated migration for:
# - New table creation
# - Foreign key constraints
# - Indexes on foreign keys
# - Unique constraints

# 4. Apply migration
alembic upgrade head
```

### Example 6: Resolving Circular Dependencies

```bash
# 1. Identify circular dependency issue
# Example: Profile -> Contact -> Profile circular reference

# 2. Refactor models to break circular dependency
# Remove one of the foreign keys causing the cycle

# 3. Generate migration
alembic revision --autogenerate -m "Fix circular dependency in profile relationships"

# 4. Apply migration
alembic upgrade head
```

## 🔗 Relationship Migration Considerations

### Understanding SQLAlchemy Relationships

When working with relationships in migrations, it's important to understand:

1. **Relationship Fields**: These are Python-only and don't create database columns
2. **Foreign Keys**: These are the actual database constraints that need migration
3. **Back References**: `back_populates` creates bidirectional relationships

### Common Relationship Migration Patterns

#### Adding a One-to-Many Relationship

```python
# In your model
class Profile(BaseModel, table=True):
    # ... other fields ...
    location_id: Optional[UUID] = Field(foreign_key="locations.id", nullable=True)

    # Relationship (Python-only, no database column)
    location: Optional[Location] = Relationship(back_populates="profiles")

class Location(BaseModel, table=True):
    # ... other fields ...

    # Back reference (Python-only, no database column)
    profiles: List[Profile] = Relationship(back_populates="location")
```

#### Migration Generated

```python
def upgrade():
    # Add foreign key column
    op.add_column('profiles', sa.Column('location_id', sa.UUID(), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key('fk_profiles_location_id', 'profiles', 'locations', ['location_id'], ['id'])

    # Add index for performance
    op.create_index('ix_profiles_location_id', 'profiles', ['location_id'])
```

### Relationship Migration Best Practices

1. **Always Review Generated Migrations**: Relationships can generate complex migrations
2. **Test Relationship Loading**: Ensure `selectinload()` works after migration
3. **Check Indexes**: Foreign keys should have indexes for performance
4. **Validate Constraints**: Ensure foreign key constraints are correct

### Troubleshooting Relationship Migrations

#### Issue: Circular Dependency Warning

```bash
# Warning: Cannot correctly sort tables; there are unresolvable cycles
```

**Solution:**

1. Identify the circular reference in your models
2. Remove one of the foreign keys causing the cycle
3. Use only one direction of the relationship
4. Regenerate migration

#### Issue: Missing Foreign Key Index

```python
# In migration file, add index if missing
def upgrade():
    # ... other operations ...
    op.create_index('ix_table_foreign_key', 'table_name', ['foreign_key_column'])
```

#### Issue: Relationship Not Loading

```python
# Ensure your queries use selectinload
from sqlalchemy.orm import selectinload

# Correct way
query = select(Profile).options(selectinload(Profile.location))

# Wrong way (will cause N+1 queries)
query = select(Profile)  # Without options
```

## 🔗 Related Documentation

- [API Documentation](./api-documentation.md)
- [Development Setup](./development-setup.md)
- [Architecture Overview](./architecture.md)

## 📞 Support

If you encounter issues with migrations:

1. Check this troubleshooting guide
2. Review Alembic logs
3. Test on a development database first
4. Contact the development team

---

**Last Updated:** $(date +%Y-%m-%d)
**Version:** 1.0.0
