# Project Structure – FastAPI + SQLModel

```text
.
├── alembic/                  # Database migrations
│   ├── versions/             # Auto-generated migration scripts
│   └── env.py
│
├── app/
│   ├── main.py               # FastAPI entrypoint
│   ├── core/                 # Core application logic
│   │   ├── config.py         # Settings, env loader
│   │   ├── security.py       # Auth utilities (JWT, password hashing)
│   │   └── logging.py        # Structured logging setup
│   │
│   ├── db/                   # Database setup
│   │   ├── session.py        # AsyncSession + sessionmaker
│   │   └── init_db.py        # Startup initialization
│   │
│   ├── models/               # SQLModel/SQLAlchemy models (DB tables)
│   │   └── user_model.py
│   │
│   ├── schemas/              # Pydantic v2 schemas (request/response)
│   │   └── user_schema.py
│   │
│   ├── routers/              # FastAPI route definitions
│   │   ├── user_routes.py
│   │   └── auth_routes.py
│   │
│   ├── services/             # Business logic layer
│   │   └── user_service.py
│   │
│   ├── utils/                # Small utility functions
│   │   ├── hashing.py
│   │   └── time_utils.py
│   │
│   ├── types/                # Shared type hints and enums
│   │   └── role_types.py
│   │
│   ├── middleware/           # Custom FastAPI middleware
│   │   └── error_handler.py
│   │
│   └── dependencies/         # FastAPI DI dependencies
│       └── auth_dependency.py
│
├── tests/                    # Unit and integration tests
│   ├── test_users.py
│   └── conftest.py
│
├── docs/                     # Project documentation
│   ├── api-documentation.md
│   └── architecture.md
│
├── .env                      # Environment variables (excluded from git)
├── .gitignore
├── .cursorignore
├── .cursorrules              # Your Cursor custom rules
├── project_structure.md       # This file
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml             # Poetry/uv/pip config
└── README.md
```

# Conventions enforced

- Snake_case filenames: `user_routes.py`, `user_schema.py`.
- RORO pattern: All functions receive objects (schemas/models) and return objects.
- Separation of concerns:
  - `models/` → database schema.
  - `schemas/` → request/response validation.
  - `routers/` → route definitions.
  - `services/` → business logic.
  - `utils/` → reusable small helpers.
  - `middleware/` → error handling, logging, etc.
  - `dependencies/` → DI wiring for sessions, auth, etc.
