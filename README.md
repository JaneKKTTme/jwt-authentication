# 🔐 Auth System: JWT + Redis Whitelist / Blacklist with RBAC

An authentication system that doesn't just *trust* JWT tokens blindly.  
Because stateless doesn't mean "can't be revoked" - meet your new security guard: **Redis** 🛡️

> *Warning:* This system actually cares about token security. Your JWTs have never been this supervised! ⚠️

## 📑 Table of Contents
- [Description](#description)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [How It Works (The Magic)](#how-it-works-the-magic)
- [Permission System](#permission-system)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Security Mechanisms](#security-mechanisms)
- [Token Leak Protection](#token-leak-protection)
- [Possible Improvements](#possible-improvements)
- [Roadmap](#roadmap)
- [License](#license)
- [Pro Tip](#pro-tip)

## <a id="description"></a> 📋 Description

Standard JWT has a fatal flaw: once issued, it lives until expiration - even if stolen.  
This system solves that by maintaining **Whitelist** and **Blacklist** in Redis, checked on **every** request.

Built with **FastAPI** (async, modern, fast), backed by **PostgreSQL** (sessions, users, audit logs), and protected by **bcrypt** + **JWT**.

## <a id="quick-start"></a> 🚀 Quick Start

### With Docker (recommended)
```bash
# Clone the project
git clone jwt-authentication
cd jwt-authentication

# Start everything (PostgreSQL + Redis + FastAPI)
docker-compose up --build

# Seed permissions (first time only - in another terminal)
docker-compose --profile seed-permissions up

# Seed test users (first time only)
docker-compose --profile seed-users up
```
Then open: `http://localhost:8000/docs` for interactive API documentation.

#### Test Users (auto-created via seed script)
| Username | Password | Role |
| -------- | ------- | ------- |
| alice | alicepass | role1 |
| bob | bobpass | role2 |
| admin | adminpass | admin |

### Without Docker (local development)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables (or use .env file)
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/auth_db
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=your-secret-key-change-in-production
export ALGORITHM=HS256
export ACCESS_TOKEN_EXPIRE_MINUTES=30

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## <a id="api-endpoints"></a> 🔌 API Endpoints

### Public Endpoints
| Method | Endpoint | Description |
| -------- | ------- | ------- |
| GET | / | API status |
| GET | /ping | Simple health check |
| POST | /login | Authenticate → get JWT |
| POST | /logout | Revoke current token |
| POST | /register | Create new user account |
| GET | /health/db | Database connectivity check |

### Protected (need Bearer token)
| Method | Endpoint | Required Permission | Description |
| -------- | ------- | ------- | ------- |
| GET | /me | Authenticated user | Get current user info |
| GET | /content/common | `content:read:common` | Common content for all roles |
| GET | /content/role1 | `content:read:role1` | Role1 exclusive content |
| GET | /content/role2 | `content:read:role2` | Role2 exclusive content |
| GET | /content/admin | `content:read:admin` | Admin dashboard |

### Admin Endpoints
| Method | Endpoint | Required Permission | Description |
| -------- | ------- | ------- | ------- |
| GET | /admin/users | `users:read` | List all active users |
| POST | /admin/users/{id}/block | `users:block` | Block user account |
| POST | /admin/users/{id}/unblock | `users:unblock` | Unblock user account |

### Example Usage
```bash
# Login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alicepass"}'

# Response: {"access_token":"eyJ...", "token_type":"bearer", "role":"role1"}

# Access protected content
curl -X GET http://localhost:8000/content/role1 \
  -H "Authorization: Bearer eyJ..."

# Logout
curl -X POST http://localhost:8000/logout \
  -F "token=eyJ..."
```

## <a id="testing"></a> 🧪 Testing
```bash
# Run all tests with Docker
docker-compose --profile testing up --build

# Or run tests locally
pytest -v --tb=short

# Run specific test file
pytest tests/test_rbac.py -v

# Run with coverage
pytest --cov=app tests/
```

### Test Coverage
- **JWT Validation** - token generation, decoding, expiration
- **Logout Mechanism** - whitelist/blacklist operations
- **RBAC** - permission checking, role-based access
- **Session Management** - session creation, revocation
- **Admin Operations** - user blocking/unblocking

## <a id="how-it-works-the-magic"></a> 🎪 How It Works (The Magic)

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Redis
    participant PostgreSQL

    Client->>API: POST /login (username/password)
    API->>PostgreSQL: verify user + bcrypt
    PostgreSQL-->>API: user found with roles
    API->>API: generate JWT with unique jti
    API->>Redis: add jti to whitelist (TTL 30min)
    API->>PostgreSQL: create session record with IP/UA
    API-->>Client: access_token

    Client->>API: GET /content/role1 (Bearer token)
    API->>Redis: is jti whitelisted?
    Redis-->>API: yes
    API->>Redis: is jti blacklisted?
    Redis-->>API: no
    API->>PostgreSQL: fetch user permissions
    PostgreSQL-->>API: permission set
    API->>API: validate required permissions
    API-->>Client: exclusive content

    Client->>API: POST /logout (token)
    API->>Redis: move jti to blacklist
    API->>PostgreSQL: mark session as revoked
    API-->>Client: logged out
```

### Why Redis?
- Sub-millisecond response time
- Automatic TTL (no cron jobs)
- Perfect for high‑throughput auth (10k+ RPS)

### Redis TTL Configuration
- **Whitelist TTL:** 30 minutes (matches `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Blacklist TTL:** 1 hour (for audit trail)

## <a id="permission-system"></a> 🎯 Permission System

Permissions follow the pattern: `{resource}:{action}`

The system implements a **granular permission-based access control** with:
- *Resources:* content, users, sessions, roles, permissions, admin, health
- *Actions:* create, read, update, delete, block, unblock, assign_role, revoke
- *Permission Registry:* Centralized metadata with dependency tracking

### Permission Examples
```python
# Content permissions
CONTENT_READ_COMMON = "content:read:common"      # All authenticated users
CONTENT_READ_ROLE1 = "content:read:role1"        # Role1 exclusive
CONTENT_READ_ROLE2 = "content:read:role2"        # Role2 exclusive
CONTENT_READ_ADMIN = "content:read:admin"        # Admin only

# User management
USERS_READ = "users:read"                        # View user list
USERS_BLOCK = "users:block"                      # Block users
USERS_UNBLOCK = "users:unblock"                  # Unblock users

# Session management
SESSIONS_READ = "sessions:read"                   # View sessions
SESSIONS_REVOKE_OTHER = "sessions:revoke:other"  # Revoke other users' sessions
```

### Default Role Permissions
| Role | Permissions |
| -------- | -------- |
| role1 | `content:read:common`, `content:read:role1` |
| role2 | `content:read:common`, `content:read:role2` |
| admin | Admin access, user management, session management, role/permission viewing, health checks |

> Note: `SESSIONS_READ`, `SESSIONS_REVOKE_OTHER`, `SESSIONS_REVOKE_ALL` permissions are defined but endpoints are TODO.

## <a id="features"></a> ✨ Features
- **JWT with Whitelist** - token must be explicitly whitelisted after login
- **Instant Revocation** - logout or admin block → token goes to Blacklist
- **Granular RBAC** - Role-Based Access Control with fine-grained permissions
- **Permission Registry** - centralized permission management with dependency validation
- **Session Tracking** - every token is logged in PostgreSQL (IP, User-Agent, timestamps)
- **Admin Endpoints** - list users, block accounts, revoke all sessions
- **Role-based Content** - role1, role2, admin with exclusive content
- **Health Checks** - for Docker orchestration (Redis + PostgreSQL)
- **Automatic Data Seeding** - seed scripts for permissions and test users

## <a id="tech-stack"></a> 🛠️ Tech Stack

| Layer | Technology |
|-------|-------------|
| **API Framework** | FastAPI (async) |
| **Token Storage** | Redis 7 (whitelist/blacklist with TTL) |
| **Persistent DB** | PostgreSQL 15 + SQLAlchemy 2.0 (asyncpg) |
| **Auth** | JWT (python-jose) + bcrypt 4.0 |
| **Testing** | pytest 7.4 + pytest-asyncio + fakeredis |
| **Container** | Docker + Docker Compose |

## <a id="project-structure"></a> 📁 Project Structure
```text
jwt-authentication/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, routes, lifespan
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # Async DB engine
│   ├── api/                 # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py          # Login, register
│   │   ├── logout.py        # Token revocation
│   │   ├── admin.py         # User management
│   │   └── content.py       # Protected content
│   └── core/                # Core business logic
│       ├── config.py        # Settings
│       ├── dependencies.py  # Auth dependencies
│       ├── permissions.py   # RBAC logic
│       ├── redis_client.py  # Redis wrapper
│       └── schemas.py       # Pydantic request/response models
├── tests/                   # Unit and integration tests
│   ├── __init__.py
│   ├── conftest.py          # Fixtures (async client, test db, mock redis)
│   ├── test_jwt.py          # JWT token validation tests
│   ├── test_logout.py       # Logout and token revocation tests
│   └── test_rbac.py         # Role and permission-based access tests
├── scripts/                 # Seeding scripts
│   ├── seed_permissions.py  # Create roles and permissions
│   └── seed_users.py        # Create test users with roles
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
└── README.ru.md
```

## <a id="database-schema"></a> 📊 Database Schema

### Core Tables
- **users** - User accounts (id, username, hashed_password, is_active, timestamps)
- **roles** - Role definitions (id, name, description, is_default)
- **permissions** - Permission definitions (id, name, resource, action)
- **sessions** - Active sessions (id, user_id, jti, ip_address, user_agent)
- **user_roles** - Many-to-many (user_id, role_id)
- **role_permissions** - Many-to-many (role_id, permission_id)

## <a id="security-mechanisms"></a> 🛡️ Security Mechanisms
| Threat | Mitigation | Status |
| -------- | ------- | ------- |
| Stolen token | Whitelist + Blacklist - immediate revocation | ✅ |
| Token replay | JTI stored in Redis, checked every request | ✅ |
| Password leak | bcrypt hashing (salt + cost factor) | ✅ |
| Session hijacking | IP + User-Agent logged, session tracking | ✅ |
| Admin abuse | Granular permission system | ✅ |
| Privilege escalation | Permission dependency validation | ✅ |
| Redis downtime | Health check + 503 error | ✅ |

## <a id="token-leak-protection"></a> 🔐 Token Leak Protection

### ❓ Where do leaks come from?
| Theft method | How it happens |
| -------- | ------- |
| XSS attack | Script steals token from localStorage |
| Traffic interception | HTTP transmitted (not HTTPS) |
| Browser vulnerabilities | Malicious extension |
| Server logs | Token appears in debug logs |
| Phishing | Fake website captures token |

### 🛡️ Protection methods
Already implemented in this project:
1. *Whitelist + Blacklist* - instant token revocation
2. *Session binding* - IP and User-Agent validation
3. *Short lifetime* - 30-minute token expiration
4. *HttpOnly cookies* - XSS protection

## <a id="possible-improvements"></a> 🛠️ Possible Improvements (Roadmap)
- **Refresh Token with rotation** - better UX than 30‑min logouts
- **Device fingerprinting** - detect token theft via changed User‑Agent/IP
- **Rate limiting** - prevent brute‑force login attacks
- **Prometheus metrics** - monitor active tokens, revocation rate
- **Two‑Factor Authentication (2FA)** - additional security layer
- **OAuth2 / OpenID Connect** - social login integration
- **Audit logging** - track all permission checks

## <a id="roadmap"></a> 🛣️ Roadmap

### Implemented ✅
- JWT authentication with whitelist/blacklist
- Complete RBAC with 40+ permissions
- Session tracking in PostgreSQL
- Admin endpoints (list, block, unblock users)
- Permission dependency validation
- Seeding scripts for initial data
- Comprehensive test suite

### Planned 🚧

#### Short-term:
- Implement `block_user` and `unblock_user` logic in `admin.py`
- Add session revocation endpoints (revoke self, revoke other, revoke all)
- Add refresh token rotation
- Rate limiting on login endpoint

#### Medium-term:
- Device fingerprinting (detect token theft)
- Audit logging (track all permission checks)
- Prometheus metrics (active sessions, token revocation rate)
- Two-Factor Authentication (2FA)

#### Long-term:
- OAuth2 / OpenID Connect (social login)
- WebAuthn (passwordless authentication)
- gRPC API for high-performance internal services
- Distributed rate limiting with Redis

## <a id="license"></a> 📜 License
MIT - use it, break it, fix it, improve it. Just keep security in mind!

## <a id="pro-tip"></a> 💡 Pro Tip
> Never log JWT tokens - not in files, not in console, not anywhere. If you need to debug, log only the jti (token ID) and the user.

And remember:
**Whitelist + Blacklist = Sleep well at night** 😴🔒

***Happy securing!*** 🔐✨
