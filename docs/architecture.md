# Architecture Overview

This document provides a comprehensive overview of the AAI Backend system architecture, design decisions, and technical implementation details.

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Database Design](#database-design)
- [API Design](#api-design)
- [Security Architecture](#security-architecture)
- [Deployment Architecture](#deployment-architecture)
- [Performance Considerations](#performance-considerations)

## 🏗️ System Overview

The AAI Backend is a modern, scalable REST API built with FastAPI and SQLModel, designed to handle user management, authentication, and profile management for the AAI platform.

### Core Features

- **User Management**: Complete CRUD operations for users
- **Profile Management**: Detailed user profiles with personal and professional information
- **Location Management**: Separate location entities for better data organization
- **Contact Management**: Multiple contact methods per profile (phone, email, etc.)
- **Job Management**: Professional experience tracking per profile
- **Relationship Optimization**: Efficient data loading with SQLAlchemy relationships
- **Authentication**: JWT-based authentication with refresh tokens
- **Authorization**: Role-based access control
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## 🛠️ Technology Stack

### Backend Framework

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLModel**: SQL databases in Python, designed for simplicity, compatibility, and robustness
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping (ORM) library
- **Alembic**: Database migration tool

### Database

- **PostgreSQL**: Primary database (production)
- **SQLite**: Development and testing database

### Authentication & Security

- **JWT**: JSON Web Tokens for authentication
- **python-jose**: JWT token handling
- **passlib**: Password hashing with bcrypt
- **python-multipart**: Form data handling

### Development & Deployment

- **Uvicorn**: ASGI server for FastAPI
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Pytest**: Testing framework

## 📁 Project Structure

```
aai_backend/
├── alembic/                    # Database migrations
│   ├── versions/              # Migration files
│   ├── env.py                 # Alembic environment
│   └── script.py.mako         # Migration template
├── docs/                      # Documentation
│   ├── README.md
│   ├── database-migrations.md
│   ├── api-documentation.md
│   ├── development-setup.md
│   └── architecture.md
├── src/                       # Source code
│   ├── core/                  # Core functionality
│   │   ├── config.py          # Configuration management
│   │   ├── db.py              # Database connection
│   │   ├── logging.py         # Logging configuration
│   │   └── security.py        # Security utilities
│   ├── models/                # Database models
│   │   ├── base.py            # Base model class
│   │   ├── user.py            # User model
│   │   └── profile.py         # Profile, Location, Contact, Job models
│   ├── schemas/               # Pydantic schemas
│   │   ├── user.py            # User schemas
│   │   ├── profile.py         # Profile schemas with relationships
│   │   ├── location.py        # Location schemas
│   │   ├── contact.py         # Contact schemas
│   │   └── job.py             # Job schemas
│   ├── routers/               # API routes
│   │   ├── auth_router.py     # Authentication routes
│   │   ├── users_router.py    # User management routes
│   │   ├── profiles_router.py # Profile management routes
│   │   ├── locations_router.py # Location management routes
│   │   ├── contacts_router.py # Contact management routes
│   │   ├── jobs_router.py     # Job management routes
│   │   └── organizations_router.py # Organization routes
│   ├── dependencies/          # FastAPI dependencies
│   ├── main.py                # Application entry point
│   └── router_setup.py        # Router configuration
├── tests/                     # Test files
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker configuration
├── requirements.txt           # Python dependencies
├── alembic.ini               # Alembic configuration
└── README.md                 # Project README
```

## 🗄️ Database Design

### Entity Relationship Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      Users      │    │    Profiles     │    │   Locations     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (UUID, PK)   │◄───┤ id (UUID, PK)   │    │ id (UUID, PK)   │
│ username        │    │ user_id (FK)    │    │ country         │
│ email           │    │ first_name      │    │ state_province  │
│ password_hash   │    │ last_name       │    │ city            │
│ is_active       │    │ date_of_birth   │    │ postal_code     │
│ is_super_admin  │    │ gender          │    │ is_active       │
│ created_at      │    │ location_id (FK)│◄───┤ created_at      │
│ updated_at      │    │ bio             │    │ updated_at      │
│ last_login_at   │    │ profile_picture_url │ │ deactivated_at  │
└─────────────────┘    │ is_public       │    └─────────────────┘
                       │ allow_contact   │
                       │ is_active       │
                       │ created_at      │
                       │ updated_at      │
                       │ deactivated_at  │
                       └─────────────────┘
                                │
                                │
                    ┌───────────┼───────────┐
                    │           │           │
            ┌───────▼──────┐    │    ┌──────▼──────┐
            │   Contacts   │    │    │    Jobs      │
            ├──────────────┤    │    ├──────────────┤
            │ id (UUID, PK)│    │    │ id (UUID, PK)│
            │ profile_id(FK)│◄──┘    │ profile_id(FK)│◄──┘
            │ type         │         │ title         │
            │ value        │         │ company       │
            │ is_primary   │         │ industry      │
            │ is_active    │         │ start_date    │
            │ created_at   │         │ end_date      │
            │ updated_at   │         │ is_active     │
            │ deactivated_at│        │ created_at    │
            └──────────────┘         │ updated_at    │
                                     │ deactivated_at│
                                     └──────────────┘
```

### Key Design Decisions

1. **UUID Primary Keys**: Using UUIDs instead of auto-incrementing integers for better security and distributed system compatibility
2. **Soft Deletes**: All entities are soft-deleted (is_active=False) to maintain data integrity
3. **One-to-One Relationship**: Each user has exactly one profile
4. **Normalized Design**: Separate tables for locations, contacts, and jobs to avoid data redundancy
5. **One-to-Many Relationships**: Profile can have multiple contacts and jobs, but only one location
6. **Audit Fields**: All tables include created_at, updated_at, deactivated_at timestamps
7. **Indexing**: Strategic indexes on frequently queried fields (email, username, user_id, profile_id)
8. **Relationship Optimization**: Uses SQLAlchemy relationships for efficient data loading

## 🔌 API Design

### RESTful Principles

- **Resource-based URLs**: `/api/v1/users/`, `/api/v1/profiles/`
- **HTTP Methods**: GET, POST, PUT, DELETE, PATCH
- **Status Codes**: Proper HTTP status codes for different scenarios
- **JSON**: Consistent JSON request/response format

### API Versioning

- **URL Versioning**: `/api/v1/` prefix for all endpoints
- **Backward Compatibility**: Maintained through versioning strategy

### Response Format

```json
{
  "data": [...],
  "total": 100,
  "page": 1,
  "size": 10,
  "pages": 10
}
```

### Error Handling

```json
{
  "detail": "Error message description"
}
```

## 🔐 Security Architecture

### Authentication Flow

1. **Registration**: User provides email, username, password
2. **Password Hashing**: bcrypt with salt rounds
3. **JWT Generation**: Access token (30 min) + Refresh token (7 days)
4. **Token Validation**: Middleware validates JWT on protected routes
5. **Token Refresh**: Refresh token used to generate new access token

### Security Measures

- **Password Hashing**: bcrypt with configurable salt rounds
- **JWT Security**: Signed tokens with secret key
- **CORS Configuration**: Configurable allowed origins
- **Input Validation**: Pydantic models for request validation
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries

### Authorization Levels

- **Public Endpoints**: Registration, login, health check
- **Authenticated Endpoints**: All CRUD operations require valid JWT
- **Admin Endpoints**: Super admin role for administrative functions

## 🚀 Deployment Architecture

### Development Environment

```
┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │───►│   PostgreSQL    │
│   (Uvicorn)     │    │   (Docker)      │
│   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘
```

### Production Environment

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │───►│   FastAPI App   │───►│   PostgreSQL    │
│   (Nginx)       │    │   (Docker)      │    │   (Managed)     │
│   Port: 80/443  │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Docker Configuration

- **Multi-stage Build**: Optimized production image
- **Health Checks**: Container health monitoring
- **Environment Variables**: Configuration through environment
- **Volume Mounts**: Persistent data storage

## ⚡ Performance Considerations

### Database Optimization

- **Connection Pooling**: SQLAlchemy connection pool
- **Query Optimization**: Efficient queries with proper indexing
- **Pagination**: Limit result sets to prevent memory issues
- **Eager Loading**: Uses `selectinload()` to efficiently load relationships
- **Relationship Caching**: SQLAlchemy relationship caching for repeated access
- **Index Strategy**: Optimized indexes on foreign keys and frequently queried fields

### Caching Strategy

- **Application-level**: In-memory caching for frequently accessed data
- **Database-level**: Query result caching
- **CDN**: Static asset caching (if applicable)

### Monitoring & Logging

- **Structured Logging**: JSON-formatted logs for easy parsing
- **Health Checks**: Application and database health monitoring
- **Metrics**: Performance metrics collection
- **Error Tracking**: Comprehensive error logging and tracking

## 🔄 Data Flow

### User Registration Flow

```
1. Client → POST /auth/register
2. Validate input data
3. Check for existing user
4. Hash password
5. Create user record
6. Generate JWT tokens
7. Return tokens to client
```

### User Authentication Flow

```
1. Client → POST /auth/login
2. Validate credentials
3. Verify password hash
4. Generate JWT tokens
5. Update last_login_at
6. Return tokens to client
```

### Protected Route Access

```
1. Client → GET /users/ (with JWT)
2. Validate JWT token
3. Extract user information
4. Execute business logic
5. Return response to client
```

## 🧪 Testing Strategy

### Test Types

- **Unit Tests**: Individual function/class testing
- **Integration Tests**: API endpoint testing
- **Database Tests**: Model and migration testing
- **Security Tests**: Authentication and authorization testing

### Test Database

- **Separate Database**: Isolated test environment
- **Test Fixtures**: Reusable test data
- **Migration Testing**: Verify migrations work correctly

## 📊 Scalability Considerations

### Horizontal Scaling

- **Stateless Design**: No server-side session storage
- **Load Balancing**: Multiple application instances
- **Database Scaling**: Read replicas for read-heavy workloads

### Vertical Scaling

- **Resource Optimization**: Efficient memory and CPU usage
- **Connection Pooling**: Optimized database connections
- **Caching**: Reduce database load

## 🔗 Related Documentation

- [Database Migration Guide](./database-migrations.md)
- [API Documentation](./api-documentation.md)
- [Development Setup](./development-setup.md)

## 📈 Future Enhancements

### Planned Features

- **Redis Caching**: Distributed caching layer
- **Message Queue**: Asynchronous task processing
- **Microservices**: Service decomposition
- **API Gateway**: Centralized API management
- **Monitoring**: Advanced monitoring and alerting

### Performance Improvements

- **Database Sharding**: Horizontal database scaling
- **CDN Integration**: Static asset delivery
- **GraphQL**: Alternative to REST API
- **Real-time Features**: WebSocket support

---

**Last Updated:** $(date +%Y-%m-%d)
**Version:** 1.0.0
