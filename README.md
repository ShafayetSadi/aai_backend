# AAI Backend

A modern FastAPI-based backend service with user management, authentication, and profile management features.

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
git clone https://github.com/ShafayetSadi/aai_backend.git
cd aai_backend
docker-compose up -d
```

API available at `http://localhost:8000`

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start server
uvicorn src.main:app --reload
```

## 📚 Features

- **User Management** - Complete CRUD operations for users
- **Profile Management** - Detailed user profiles with personal/professional info
- **JWT Authentication** - Secure token-based authentication
- **RESTful API** - Well-documented REST endpoints
- **Database Migrations** - Alembic-powered schema management

## 🛠️ Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLModel** - SQL databases in Python
- **PostgreSQL** - Primary database
- **JWT** - Authentication tokens
- **Alembic** - Database migrations

## 📖 API Documentation

- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔧 Development

```bash
# Run tests
pytest

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## 📋 Documentation

For detailed documentation, setup guides, API reference, and deployment instructions, see the [docs/](./docs/) folder:

- [Development Setup](./docs/development-setup.md)
- [API Documentation](./docs/api-documentation.md)
- [Database Migrations](./docs/database-migrations.md)
- [Architecture Overview](./docs/architecture.md)
- [Deployment Guide](./docs/deployment.md)

## 📄 License

This project is private and proprietary.
