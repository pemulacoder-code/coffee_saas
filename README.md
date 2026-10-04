# Coffee SaaS

Multi-tenant SaaS platform for coffee shop management.

## Tech Stack

### Backend

* Python
* FastAPI
* Uvicorn
* SQLAlchemy Async
* PostgreSQL
* Alembic
* Redis
* Pydantic Settings

### Infrastructure

* Docker
* Docker Compose

### Frontend

* Flutter

## Architecture

Coffee SaaS is designed as a scalable modular monolith with multi-tenant architecture.

High-level architecture:

```text
Flutter
   │
   ▼
FastAPI
   │
   ├── PostgreSQL
   │
   └── Redis
```

Tenant structure:

```text
Organization
   │
   ├── Branch
   │
   ├── Users
   │
   └── Business Data
```

Each organization represents a tenant and tenant data must remain strictly isolated.

## Project Structure

```text
coffee_saas/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── modules/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements.lock.txt
│
├── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
└── README.md
```

## Requirements

Install the following before starting development:

* Docker Desktop
* Git
* Python 3.14+
* Flutter SDK

Docker Desktop must be running.

## Environment Configuration

Create a local environment file:

```bash
cp .env.example .env
```

The `.env` file contains local development configuration and must not be committed to Git.

## Start Development Environment

Start PostgreSQL, Redis, and the FastAPI API:

```bash
docker compose up -d
```

Check running services:

```bash
docker compose ps
```

Expected services:

```text
coffee_saas_postgres
coffee_saas_redis
coffee_saas_api
```

## API

The API is available at:

```text
http://127.0.0.1:8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

Root endpoint:

```bash
curl http://127.0.0.1:8000/
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

Alternative documentation:

```text
http://127.0.0.1:8000/redoc
```

## Docker Commands

Start services:

```bash
docker compose up -d
```

Stop services:

```bash
docker compose stop
```

Restart API:

```bash
docker compose restart api
```

View service status:

```bash
docker compose ps
```

View API logs:

```bash
docker compose logs -f api
```

View PostgreSQL logs:

```bash
docker compose logs -f postgres
```

View Redis logs:

```bash
docker compose logs -f redis
```

Rebuild the API image:

```bash
docker compose build api
```

## Database

PostgreSQL is available to the host at:

```text
localhost:5432
```

Inside the Docker network, the API connects to PostgreSQL using:

```text
postgres:5432
```

Database:

```text
coffee_saas
```

User:

```text
postgres
```

## Redis

Redis is available to the host at:

```text
localhost:6379
```

Inside the Docker network, the API connects to Redis using:

```text
redis:6379
```

## Database Migrations

Alembic configuration is located at:

```text
alembic.ini
```

Migration files are located at:

```text
backend/alembic/
```

Create a migration:

```bash
python -m alembic revision --autogenerate -m "migration message"
```

Apply migrations:

```bash
python -m alembic upgrade head
```

Check current migration:

```bash
python -m alembic current
```

View migration history:

```bash
python -m alembic history
```

## Development Principles

The project follows these principles:

1. Multi-tenant data isolation.
2. Modular monolith architecture.
3. Async database access.
4. UUID identifiers.
5. UTC timezone-aware timestamps.
6. Explicit database migrations.
7. Environment-based configuration.
8. Containerized local development.
9. Automated testing.
10. Security-first design.

## Development Roadmap

### Step 0 — Planning & Architecture

Architecture, business requirements, and technical decisions.

### Step 1 — Project Foundation

Development environment, Docker, PostgreSQL, Redis, FastAPI, SQLAlchemy, Alembic, logging, exception handling, CORS, and testing foundation.

### Step 2 — Database & Migration

Database models, migrations, indexes, constraints, and database conventions.

### Step 3 — Authentication & Authorization

Authentication, JWT, password security, refresh tokens, and authorization.

### Step 4 — Multi-Tenant Architecture

Tenant context, tenant isolation, and tenant-aware database access.

### Step 5 — Organization Management

Organization creation and management.

### Step 6 — Branch Management

Coffee shop branch management.

### Step 7 — User, Role & Permission

Users, roles, permissions, and access control.

### Step 8 — Product / Menu Management

Products, categories, variants, modifiers, and menu management.

### Step 9 — Inventory Management

Stock, ingredients, suppliers, stock movements, and inventory control.

### Step 10 — Customer Management

Customer profiles and customer history.

### Step 11 — Order Management

POS orders, order items, order status, kitchen/bar workflow, and order history.

### Step 12 — Payment Management

Payment methods, transactions, and payment reconciliation.

### Step 13 — Table / Dine-in Management

Tables, seating, and dine-in orders.

### Step 14 — Reservation Management

Customer reservations and booking management.

### Step 15 — Discount & Promotion

Discounts, promotions, vouchers, and campaign rules.

### Step 16 — Reports & Dashboard

Business reports, analytics, and dashboards.

### Step 17 — Notification

Operational and customer notifications.

### Step 18 — Subscription & SaaS Billing

Tenant subscriptions, plans, billing, and SaaS limits.

### Step 19 — Flutter Application

Desktop, tablet, and mobile applications based on role and workflow.

### Step 20 — Testing & Security

Unit testing, integration testing, tenant isolation testing, and security hardening.

### Step 21 — Production Docker

Production containerization and deployment configuration.

### Step 22 — CI/CD & Deployment

Automated build, testing, and deployment pipelines.

### Step 23 — Monitoring & Logging

Application monitoring, metrics, centralized logging, and alerts.

### Step 24 — Production Hardening

Performance, reliability, security, backups, disaster recovery, and production readiness.

## Current Status

Step 1 — Project Foundation

```text
Development Environment       PASS
Repository                    PASS
Backend Structure             PASS
Python Environment            PASS
Dependencies                  PASS
Docker Compose                PASS
PostgreSQL                    PASS
Redis                         PASS
Environment Configuration     PASS
FastAPI Application            PASS
Health Check                  PASS
API Router                    PASS
SQLAlchemy Engine             PASS
Async Session                 PASS
Declarative Base              PASS
UUID Strategy                 PASS
Timestamp Convention          PASS
Base Model                    PASS
Alembic                       PASS
Redis Client                  PASS
Logging                       PASS
Exception Handling            PASS
CORS                          PASS
Application Lifecycle         PASS
Dockerize FastAPI             PASS
Docker Networking             PASS
Gitignore / Repository        PASS
README                        IN PROGRESS
Testing Foundation            TODO
Integration Test              TODO
API Documentation             TODO
Git Commit                    TODO
Final Verification            TODO
```
