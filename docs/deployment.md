# Deployment Guide

This guide covers the deployment process for the AAI Backend application in various environments.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Database Migration](#database-migration)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedures](#rollback-procedures)

## 🔧 Prerequisites

### Required Software

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **PostgreSQL** 15+ (if not using containerized database)
- **Git** (for code deployment)

### Required Access

- **Server Access**: SSH access to deployment server
- **Database Access**: Database administration privileges
- **Domain/DNS**: Domain name and DNS configuration (for production)

## ⚙️ Environment Configuration

### 1. Environment Variables

Create environment-specific configuration files:

#### Development (.env.development)

```env
# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/aai_backend_dev

# Security
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
APP_NAME=AAI Backend
ENVIRONMENT=development
DEBUG=true

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Logging
LOG_LEVEL=DEBUG
```

#### Production (.env.production)

```env
# Database
DATABASE_URL=postgresql+asyncpg://username:password@prod-db-host:5432/aai_backend

# Security
SECRET_KEY=your-super-secure-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=1

# Application
APP_NAME=AAI Backend
ENVIRONMENT=production
DEBUG=false

# CORS
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]

# Logging
LOG_LEVEL=INFO
```

### 2. Docker Compose Configuration

#### docker-compose.yml

```yaml
version: "3.8"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://aai_user:password@db:5432/aai_backend
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=aai_backend
      - POSTGRES_USER=aai_user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
```

#### docker-compose.prod.yml

```yaml
version: "3.8"

services:
  app:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

volumes:
  postgres_data:
```

## 🐳 Docker Deployment

### 1. Build and Run Locally

```bash
# Build the Docker image
docker build -t aai-backend .

# Run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### 2. Production Build

```bash
# Build production image
docker build -t aai-backend:latest .

# Tag for registry
docker tag aai-backend:latest your-registry.com/aai-backend:latest

# Push to registry
docker push your-registry.com/aai-backend:latest
```

### 3. Docker Health Checks

Add health checks to your Dockerfile:

```dockerfile
# Add to Dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

## 🚀 Production Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### 2. Application Deployment

```bash
# Clone repository
git clone <repository-url>
cd aai_backend

# Create production environment file
cp .env.example .env.production
nano .env.production

# Deploy with Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check deployment status
docker-compose ps
```

### 3. Nginx Configuration

#### nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

    server {
        listen 443 ssl;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 4. SSL Certificate Setup

```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🗄️ Database Migration

### 1. Pre-deployment Migration

```bash
# Backup production database
pg_dump -h localhost -U username -d database_name > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migrations
alembic upgrade head

# Verify migration success
alembic current
```

### 2. Zero-downtime Migration

```bash
# 1. Deploy new application version
docker-compose up -d app

# 2. Run migrations
docker-compose exec app alembic upgrade head

# 3. Verify application health
curl http://localhost:8000/health
```

## 📊 Monitoring & Logging

### 1. Application Logs

```bash
# View application logs
docker-compose logs -f app

# View specific service logs
docker-compose logs -f db

# Follow logs in real-time
tail -f logs/app.log
```

### 2. Health Monitoring

```bash
# Check application health
curl http://localhost:8000/health

# Check database connection
docker-compose exec app python -c "from src.core.db import check_db_connection; import asyncio; print(asyncio.run(check_db_connection()))"
```

### 3. Resource Monitoring

```bash
# Check container resource usage
docker stats

# Check disk usage
df -h

# Check memory usage
free -h
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check logs
docker-compose logs app

# Check environment variables
docker-compose exec app env

# Restart service
docker-compose restart app
```

#### 2. Database Connection Issues

```bash
# Check database status
docker-compose ps db

# Check database logs
docker-compose logs db

# Test database connection
docker-compose exec app python -c "from src.core.db import get_session; print('DB OK')"
```

#### 3. Migration Issues

```bash
# Check migration status
docker-compose exec app alembic current

# Check migration history
docker-compose exec app alembic history

# Rollback if needed
docker-compose exec app alembic downgrade -1
```

### Performance Issues

#### 1. High Memory Usage

```bash
# Check memory usage
docker stats

# Restart application
docker-compose restart app

# Scale application
docker-compose up -d --scale app=2
```

#### 2. Database Performance

```bash
# Check database connections
docker-compose exec db psql -U aai_user -d aai_backend -c "SELECT * FROM pg_stat_activity;"

# Check slow queries
docker-compose exec db psql -U aai_user -d aai_backend -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

## 🔄 Rollback Procedures

### 1. Application Rollback

```bash
# Stop current version
docker-compose down

# Deploy previous version
git checkout previous-version-tag
docker-compose up -d

# Verify rollback
curl http://localhost:8000/health
```

### 2. Database Rollback

```bash
# Check current migration
alembic current

# Rollback to previous migration
alembic downgrade -1

# Verify rollback
alembic current
```

### 3. Complete System Rollback

```bash
# 1. Stop all services
docker-compose down

# 2. Restore database backup
pg_restore -h localhost -U username -d database_name backup_file.sql

# 3. Deploy previous application version
git checkout previous-version-tag
docker-compose up -d

# 4. Verify system health
curl http://localhost:8000/health
```

## 🔒 Security Considerations

### 1. Environment Security

- Use strong, unique passwords
- Rotate secrets regularly
- Use environment variables for sensitive data
- Enable firewall rules

### 2. Database Security

- Use SSL connections
- Regular security updates
- Backup encryption
- Access control

### 3. Application Security

- Regular dependency updates
- Security headers
- Rate limiting
- Input validation

## 📈 Scaling Considerations

### 1. Horizontal Scaling

```bash
# Scale application instances
docker-compose up -d --scale app=3

# Use load balancer
# Configure nginx for multiple upstream servers
```

### 2. Database Scaling

- Read replicas for read-heavy workloads
- Connection pooling
- Query optimization
- Indexing strategy

## 🔗 Related Documentation

- [Database Migration Guide](./database-migrations.md)
- [API Documentation](./api-documentation.md)
- [Development Setup](./development-setup.md)
- [Architecture Overview](./architecture.md)

---

**Last Updated:** $(date +%Y-%m-%d)
**Version:** 1.0.0
