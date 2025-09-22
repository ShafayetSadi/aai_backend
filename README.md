# AAI Backend

A FastAPI-based backend service for an AI-powered application with user authentication, organization management, and staff scheduling features.

## Features

- **Authentication & Authorization**

  - User registration and login
  - JWT-based access and refresh tokens
  - Role-based access control (RBAC)
  - Password hashing with bcrypt

- **Organization Management**

  - Create and manage organizations
  - Invite members with different roles (owner, manager, member)
  - Organization categorization and subcategorization

- **Staff Management**

  - Staff scheduling system
  - Availability management
  - Role-based permissions

- **Database**
  - PostgreSQL with async support
  - SQLModel for ORM
  - Alembic for database migrations

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with asyncpg
- **ORM**: SQLModel
- **Authentication**: JWT with python-jose
- **Password Hashing**: Passlib with bcrypt
- **Migrations**: Alembic
- **Testing**: pytest with async support

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Using Docker Compose (Recommended)

1. Clone the repository:

```bash
git clone https://github.com/ShafayetSadi/aai_backend.git
cd aai_backend
```

2. Start the services:

```bash
docker-compose up -d
```

The API will be available at `http://localhost:8000`

### Manual Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run database migrations:

```bash
alembic upgrade head
```

4. Start the development server:

```bash
uvicorn src.main:app --reload
```

## API Documentation

Once the server is running, you can access:

- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`

## Environment Variables

| Variable                      | Description                  | Default  |
| ----------------------------- | ---------------------------- | -------- |
| `DATABASE_URL`                | PostgreSQL connection string | Required |
| `JWT_SECRET`                  | Secret key for JWT tokens    | Required |
| `ALGORITHM`                   | JWT algorithm                | HS256    |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry          | 15       |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Refresh token expiry         | 7        |
| `CORS_ORIGINS`                | Allowed CORS origins         | \*       |

## API Endpoints

### Authentication (`/auth`)

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info

### Organizations (`/organizations`)

- `POST /organizations` - Create organization
- `POST /organizations/{org_id}/invite` - Invite member
- `GET /organizations/{org_id}/members` - List members

### Staff (`/staff`)

- `GET /staff/me/schedule` - Get my schedule
- `POST /staff/me/availability` - Update availability

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## License

This project is private and proprietary.
