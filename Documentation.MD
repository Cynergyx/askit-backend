# Askit Backend Documentation

## Overview

This backend provides:

- **User authentication** (JWT, SSO)
- **Role and permission management** (RBAC)
- **Audit logging** (actions, permission changes)
- **Multi-tenant support** (organization isolation)
- **Security utilities** (rate limiting, password policies, data masking)
- **RESTful API** with modular blueprints

---

## Project Structure

```
config.py                # App configuration
run.py                   # App entrypoint (to be completed)
src/
  app.py                 # Flask app factory, extension setup
  controllers/           # Business logic for each resource
  middleware/            # Auth, RBAC, tenant isolation decorators
  models/                # SQLAlchemy models (User, Role, Permission, etc.)
  routes/                # API route blueprints
  services/              # Service layer (auth, audit, RBAC, SSO, etc.)
  utils/                 # Utilities (database, decorators, security)
requirements.txt         # Python dependencies
.env                     # Environment variables (secrets, DB, etc.)
```

---

## How to Run

1. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**  
   Copy `.env` to your environment or export variables manually.

3. **Initialize the database**  
   (Assuming PostgreSQL is running and configured)
   ```bash
   flask db upgrade
   ```

4. **Run the application**  
   Complete `run.py` with:
   ```python
   from src.app import create_app
   app = create_app()
   if __name__ == "__main__":
       app.run(host="0.0.0.0", port=5000)
   ```
   Then start:
   ```bash
   python run.py
   ```

---

## API Endpoints & Example Payloads

### Auth

- **POST `/api/auth/login`**  
  _Standard login_
  ```json
  {
    "email": "user@example.com",
    "password": "Password123!",
    "organization": "example-org"
  }
  ```
  _Response:_  
  ```json
  {
    "access_token": "...",
    "refresh_token": "...",
    "user": { ... }
  }
  ```

- **POST `/api/auth/register`**  
  _Register new user_
  ```json
  {
    "email": "newuser@example.com",
    "password": "Password123!",
    "first_name": "John",
    "last_name": "Doe",
    "organization": "example-org"
  }
  ```

- **POST `/api/auth/refresh`**  
  _Refresh JWT token (requires refresh token in header)_

- **POST `/api/auth/sso`**  
  _SSO login (OAuth2, SAML, LDAP)_
  ```json
  {
    "provider": "google",
    "organization": "example-org",
    "code": "oauth2-code"
  }
  ```

- **POST `/api/auth/logout`**  
  _Logout (JWT required)_

---

### Users

- **GET `/api/users/`**  
  _List users (pagination, search)_
  ```
  /api/users/?page=1&per_page=20&search=alice
  ```

- **POST `/api/users/`**  
  _Create user_
  ```json
  {
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Smith"
  }
  ```

- **GET `/api/users/<user_id>`**  
  _Get user details_

- **PUT `/api/users/<user_id>`**  
  _Update user_

- **DELETE `/api/users/<user_id>`**  
  _Delete user_

- **POST `/api/users/<user_id>/roles`**  
  _Assign role to user_
  ```json
  {
    "role_id": "role-uuid"
  }
  ```

- **DELETE `/api/users/<user_id>/roles`**  
  _Revoke role from user_
  ```json
  {
    "role_id": "role-uuid"
  }
  ```

---

### Roles & Permissions

- **GET `/api/roles/`**  
  _List roles_

- **POST `/api/roles/`**  
  _Create role_
  ```json
  {
    "name": "manager",
    "display_name": "Manager",
    "description": "Manages stuff"
  }
  ```

- **GET `/api/roles/<role_id>`**  
  _Get role details_

- **PUT `/api/roles/<role_id>`**  
  _Update role_

- **DELETE `/api/roles/<role_id>`**  
  _Delete role_

- **GET `/api/roles/permissions`**  
  _List all permissions_

- **POST `/api/roles/<role_id>/permissions`**  
  _Assign permission to role_
  ```json
  {
    "permission_id": "perm-uuid"
  }
  ```

- **DELETE `/api/roles/<role_id>/permissions`**  
  _Revoke permission from role_
  ```json
  {
    "permission_id": "perm-uuid"
  }
  ```

---

### Audit

- **GET `/api/audit/logs`**  
  _Query audit logs (filter by user, action, date range)_
  ```
  /api/audit/logs?user_id=...&action=LOGIN&start_date=2024-01-01&end_date=2024-12-31&limit=50
  ```

- **GET `/api/audit/permissions`**  
  _Permission change logs_
  ```
  /api/audit/permissions?target_user_id=...&limit=20
  ```

- **GET `/api/audit/summary`**  
  _Summary/statistics for last 30 days_

---

## Features Explained

### 1. **Authentication & SSO**
- JWT-based authentication with access/refresh tokens.
- SSO support (OAuth2, SAML, LDAP) via `SSOService`.
- Organization context is always required for login.

### 2. **RBAC (Role-Based Access Control)**
- Users have roles; roles have permissions.
- Fine-grained permission checks via decorators (`require_permission`, `require_role`).
- Row-level and column-level security supported.

### 3. **Audit Logging**
- All sensitive actions are logged (`AuditLog`, `PermissionChangeLog`).
- Query logs for compliance and monitoring.

### 4. **Multi-Tenancy**
- Each request is scoped to an organization (tenant).
- Tenant isolation via middleware (`tenant_isolation`).

### 5. **Security Utilities**
- Password complexity enforcement.
- Rate limiting (per user, per endpoint).
- Data masking and encryption for sensitive fields.
- Security headers and CSRF protection.

### 6. **Extensible Service Layer**
- Business logic is separated into services for maintainability.
- Easy to add new features or integrations.

---

## How to Extend

- **Add new endpoints:**  
  Create a controller method, add a route in the corresponding blueprint.

- **Add new models:**  
  Define in `src/models/`, migrate with Flask-Migrate.

- **Add new permissions/roles:**  
  Insert into the `permissions` and `roles` tables, or via API.

---

## Notes

- All endpoints (except login/register/SSO) require JWT authentication and organization context.
- Use the `Authorization: Bearer <token>` header for protected endpoints.
- For SSO, you must configure provider credentials in your environment or config.

---

## Example: Assigning a Role

1. **Login as admin, get JWT**
2. **POST** `/api/users/<user_id>/roles` with:
   ```json
   { "role_id": "role-uuid" }
   ```
   _Requires `role.assign` permission._

---

## Example: Querying Audit Logs

**GET** `/api/audit/logs?user_id=...&action=LOGIN&limit=10`

Returns the last 10 login actions for the specified user.

---

## Final Checklist

- [x] Modular, extensible Flask app
- [x] JWT & SSO authentication
- [x] RBAC with fine-grained permissions
- [x] Multi-tenant support
- [x] Audit logging
- [x] Security best practices
- [x] RESTful API with blueprints

---

**To make it work:**  
- Complete any missing controller/service logic as needed.
- Ensure your database and environment variables are set up.
- Run the app and use the documented endpoints with the example payloads.
