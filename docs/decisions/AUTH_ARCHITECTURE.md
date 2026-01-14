# Authentication Architecture

## Overview

ForgeWorks implements JWT-based authentication with refresh token rotation for secure, stateless authentication.

## Architecture Decision

### Why JWT?
- **Stateless**: No server-side session storage required
- **Scalable**: Works across multiple backend instances
- **Standard**: Industry-standard, well-supported libraries
- **Flexible**: Contains claims for authorization

### Token Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    Token Flow                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │  Login   │───▶│  Access  │───▶│   API    │               │
│  │ Request  │    │  Token   │    │ Request  │               │
│  └──────────┘    └──────────┘    └──────────┘               │
│       │              │                │                      │
│       │              │ (15 min)       │                      │
│       │              ▼                ▼                      │
│       │         ┌──────────┐    ┌──────────┐               │
│       └────────▶│ Refresh  │───▶│  Renew   │               │
│                 │  Token   │    │  Access  │               │
│                 └──────────┘    └──────────┘               │
│                      │ (7 days)                             │
│                      ▼                                       │
│                 ┌──────────┐                                │
│                 │  Rotate  │                                │
│                 │  Tokens  │                                │
│                 └──────────┘                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Token Specifications

| Token | Lifetime | Storage | Purpose |
|-------|----------|---------|---------|
| Access Token | 15 minutes | Memory/Header | API authentication |
| Refresh Token | 7 days | HTTP-only cookie | Token renewal |

## Data Model

### User Entity

```python
class User(Base):
    __tablename__ = "users"

    id: UUID (PK)
    email: str (unique, indexed)
    hashed_password: str
    full_name: str
    role: UserRole (enum: admin, user, viewer)
    is_active: bool (default: True)
    is_verified: bool (default: False)
    created_at: datetime
    updated_at: datetime
    last_login: datetime (nullable)
```

### RefreshToken Entity

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: UUID (PK)
    user_id: UUID (FK -> users.id)
    token_hash: str (indexed, SHA-256 hash)
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime (nullable)
    replaced_by: str (nullable, hash of replacement token for audit trail)
```

## API Endpoints

### Authentication Routes

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/register` | Create new user | Public |
| POST | `/api/v1/auth/login` | Authenticate user | Public |
| POST | `/api/v1/auth/refresh` | Refresh access token | Cookie |
| POST | `/api/v1/auth/logout` | Revoke refresh token | Cookie |
| GET | `/api/v1/auth/me` | Get current user | Bearer |
| PATCH | `/api/v1/auth/me` | Update current user | Bearer |
| POST | `/api/v1/auth/change-password` | Change password | Bearer |

### Request/Response Examples

#### Register
```json
// POST /api/v1/auth/register
// Request
{
  "email": "user@example.com",
  "password": "SecureP@ss123",
  "full_name": "John Doe"
}

// Response 201
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_verified": false,
  "created_at": "2025-01-14T..."
}
```

#### Login
```json
// POST /api/v1/auth/login
// Request
{
  "email": "user@example.com",
  "password": "SecureP@ss123"
}

// Response 200
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "user"
  }
}
// + Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Lax
```

## Security Measures

### Password Security
- **Hashing**: bcrypt (passlib with auto-tuning)
- **Requirements**: Min 8 chars (enforced via Pydantic validation)

### Token Security
- **Access Token**: Signed with HS256, short-lived (15 min)
- **Refresh Token**: Random bytes, hashed in DB
- **Rotation**: New refresh token on each renewal
- **Revocation**: Immediate on logout, cascading on compromise

### Headers
```
Authorization: Bearer <access_token>
X-Request-ID: <correlation_id>
```

## Implementation Files

```
src/backend/app/
├── db/models/
│   └── user.py              # User & RefreshToken models
├── schemas/
│   └── auth.py              # Pydantic schemas
├── api/
│   ├── routes/
│   │   └── auth.py          # Auth endpoints
│   └── deps.py              # Auth dependencies (CurrentUser, etc.)
├── core/
│   └── security.py          # JWT & password utilities
└── crud/
    └── user.py              # User CRUD operations
```

## Frontend Integration

### Auth Context
```typescript
interface AuthContext {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
}
```

### Protected Routes
```typescript
// Higher-order component
const withAuth = (Component) => {
  return (props) => {
    const { isAuthenticated, isLoading } = useAuth();
    if (isLoading) return <LoadingSpinner />;
    if (!isAuthenticated) return <Navigate to="/login" />;
    return <Component {...props} />;
  };
};
```

## Configuration

### Environment Variables
```env
# JWT Settings (via Settings class)
SECRET_KEY=<random-256-bit-key>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Migration Plan

1. Create User and RefreshToken tables
2. Add auth routes (public endpoints first)
3. Implement middleware for protected routes
4. Update existing routes with auth requirements
5. Build frontend auth components
6. Integrate with existing dashboard

## Role-Based Access Control (Future)

| Role | Permissions |
|------|-------------|
| admin | Full access, user management |
| user | CRUD on own resources, read all |
| viewer | Read-only access |

---

**Status**: Architecture Approved
**Author**: Claude Opus 4.5
**Date**: 2025-01-14
