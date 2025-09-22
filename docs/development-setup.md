# Development Setup Guide

This guide will help you set up the AAI Backend development environment on your local machine.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Development Tools](#development-tools)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### Required Software

- **Python 3.12+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **Docker & Docker Compose** - [Download](https://www.docker.com/get-started)
- **PostgreSQL 15+** (if not using Docker) - [Download](https://www.postgresql.org/download/)

### Recommended Tools

- **VS Code** - [Download](https://code.visualstudio.com/)
- **Postman** - [Download](https://www.postman.com/downloads/)
- **pgAdmin** - [Download](https://www.pgadmin.org/download/)

## 🚀 Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd aai_backend
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install project dependencies
pip install -r requirements.txt

# Install development dependencies (if available)
pip install -r requirements-dev.txt
```

### 4. Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

**Required Environment Variables:**

```env
# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/aai_backend

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
APP_NAME=AAI Backend
ENVIRONMENT=development
DEBUG=true

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

## 🗄️ Database Setup

### Option 1: Using Docker (Recommended)

```bash
# Start PostgreSQL with Docker Compose
docker-compose up -d postgres

# Check if database is running
docker-compose ps
```

### Option 2: Local PostgreSQL Installation

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

```sql
-- In PostgreSQL shell
CREATE DATABASE aai_backend;
CREATE USER aai_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE aai_backend TO aai_user;
\q
```

### 3. Run Database Migrations

```bash
# Check current migration status
alembic current

# Run migrations
alembic upgrade head

# Verify migration success
alembic current
```

## 🏃 Running the Application

### 1. Start the Development Server

```bash
# Using uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or using the provided script
python -m uvicorn src.main:app --reload
```

### 2. Verify Application is Running

```bash
# Check health endpoint
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs
```

### 3. Test Authentication

```bash
# Register a new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword",
    "username": "testuser"
  }'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword"
  }'
```

## 🛠️ Development Tools

### Code Formatting

```bash
# Format code with black
black src/

# Format imports with isort
isort src/

# Check code style
flake8 src/
```

### Type Checking

```bash
# Run type checking with mypy
mypy src/
```

### Linting

```bash
# Run linting
pylint src/

# Or use ruff (faster)
ruff check src/
ruff format src/
```

### Pre-commit Hooks (Optional)

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Test Database Setup

```bash
# Create test database
createdb aai_backend_test

# Set test environment
export TEST_DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/aai_backend_test

# Run migrations on test database
alembic upgrade head
```

## 📝 Development Workflow

### 1. Making Changes

```bash
# Create a new branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Run tests
pytest

# Format code
black src/
isort src/

# Commit changes
git add .
git commit -m "Add your feature description"
```

### 2. Database Changes

```bash
# After modifying models, create migration
alembic revision --autogenerate -m "Description of changes"

# Review generated migration
cat alembic/versions/[latest_file].py

# Apply migration
alembic upgrade head
```

### 3. API Testing

```bash
# Test endpoints with curl
curl -X GET "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer your-token"

# Or use the interactive docs
open http://localhost:8000/docs
```

## 🔍 Debugging

### Application Logs

```bash
# Run with debug logging
LOG_LEVEL=DEBUG uvicorn src.main:app --reload

# Check logs in real-time
tail -f logs/app.log
```

### Database Debugging

```bash
# Connect to database
psql -h localhost -U aai_user -d aai_backend

# Check tables
\dt

# Check specific table
\d users

# Run queries
SELECT * FROM users LIMIT 5;
```

### Common Issues

#### 1. Database Connection Issues

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -h localhost -U aai_user -d aai_backend -c "SELECT 1;"
```

#### 2. Migration Issues

```bash
# Check current migration status
alembic current

# Check migration history
alembic history

# Reset migrations (development only)
alembic downgrade base
alembic upgrade head
```

#### 3. Import Issues

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Install in development mode
pip install -e .
```

## 📚 Useful Commands

### Database Commands

```bash
# Reset database
alembic downgrade base
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Check migration status
alembic current
```

### Application Commands

```bash
# Start development server
uvicorn src.main:app --reload

# Start with specific host/port
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Start in production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Git Commands

```bash
# Check status
git status

# Add all changes
git add .

# Commit changes
git commit -m "Your commit message"

# Push changes
git push origin feature/your-feature-name
```

## 🔗 Related Documentation

- [Database Migration Guide](./database-migrations.md)
- [API Documentation](./api-documentation.md)
- [Architecture Overview](./architecture.md)

## 📞 Getting Help

If you encounter issues:

1. Check this troubleshooting guide
2. Review the logs
3. Check the API documentation
4. Contact the development team

---

**Last Updated:** $(date +%Y-%m-%d)
**Version:** 1.0.0
