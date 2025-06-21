## Detailed API Documentation

Here is the documentation for the API endpoints.

### Authentication (`/api/auth`)

#### **User Login**
-   **Endpoint**: `POST /api/auth/login`
-   **Description**: Authenticates a user with email and password for a specific organization.
-   **Request Body**:
    ```json
    {
      "email": "user@example.com",
      "password": "yourpassword",
      "organization": "my-org-domain"
    }
    ```
-   **Success Response (200 OK)**:
    ```json
    {
      "access_token": "...",
      "refresh_token": "...",
      "user": {
        "id": "user-uuid",
        "email": "user@example.com",
        "full_name": "John Doe",
        "is_active": true,
        // ... other user fields, roles, permissions
      }
    }
    ```
-   **Error Responses**:
    -   `400 Bad Request`: Missing fields.
    -   `401 Unauthorized`: Invalid credentials or organization.

#### **User Registration**
-   **Endpoint**: `POST /api/auth/register`
-   **Description**: Registers a new user and organization.
-   **Request Body**:
    ```json
    {
      "email": "new.user@example.com",
      "password": "StrongPassword123!",
      "first_name": "Jane",
      "last_name": "Doe",
      "organization": "new-org-domain"
    }
    ```
-   **Success Response (201 Created)**:
    ```json
    {
      "user": {
        "id": "new-user-uuid",
        "email": "new.user@example.com",
        "full_name": "Jane Doe",
        // ... other user fields
      }
    }
    ```
-   **Error Responses**:
    -   `400 Bad Request`: Missing fields or user/org already exists.

#### **Refresh Access Token**
-   **Endpoint**: `POST /api/auth/refresh`
-   **Description**: Issues a new access token using a valid refresh token.
-   **Authorization**: `Bearer <refresh_token>`
-   **Success Response (200 OK)**:
    ```json
    {
      "access_token": "new-access-token"
    }
    ```
-   **Error Responses**:
    -   `401 Unauthorized`: Invalid or expired refresh token.

### Users (`/api/users`)

#### **Get All Users**
-   **Endpoint**: `GET /api/users`
-   **Description**: Retrieves a paginated list of users for the current organization.
-   **Authorization**: `Bearer <access_token>`
-   **Permissions**: `user.read`
-   **Success Response (200 OK)**:
    ```json
    {
      "users": [
        { "id": "uuid1", "email": "user1@example.com", ... },
        { "id": "uuid2", "email": "user2@example.com", ... }
      ],
      "total": 2,
      "pages": 1,
      "current_page": 1
    }
    ```

#### **Get a Specific User**
-   **Endpoint**: `GET /api/users/<user_id>`
-   **Description**: Retrieves detailed information for a specific user.
-   **Authorization**: `Bearer <access_token>`
-   **Permissions**: `user.read`
-   **Success Response (200 OK)**:
    ```json
    {
      "user": {
        "id": "user-uuid",
        "email": "user@example.com",
        // ... includes roles and permissions
      }
    }
    ```

#### **Assign Role to User**
-   **Endpoint**: `POST /api/users/<user_id>/roles`
-   **Description**: Assigns a role to a user.
-   **Authorization**: `Bearer <access_token>`
-   **Permissions**: `role.assign`
-   **Request Body**:
    ```json
    {
      "role_id": "role-uuid"
    }
    ```
-   **Success Response (200 OK)**:
    ```json
    {
      "message": "Role assigned successfully"
    }
    ```

### Database Access (`/api/users/<user_id>/database-access`)

#### **Get Database Access List**
-   **Endpoint**: `GET /api/users/<user_id>/database-access`
-   **Description**: Retrieves a list of database access grants for a user.
-   **Authorization**: `Bearer <access_token>`
-   **Permissions**: `database_access.read`
-   **Success Response (200 OK)**:
    ```json
    {
      "access_list": [
        {
          "id": "access-uuid",
          "database": "customer_db",
          "granted_by": "admin-uuid",
          "granted_at": "2025-06-21T10:00:00Z",
          "expires_at": "2025-07-21T10:00:00Z",
          // ... other fields
        }
      ],
      "count": 1
    }
    ```

#### **Grant Database Access**
-   **Endpoint**: `POST /api/users/<user_id>/database-access`
-   **Description**: Grants database access to a user.
-   **Authorization**: `Bearer <access_token>`
-   **Permissions**: `database_access.grant`
-   **Request Body**:
    ```json
    {
      "database": "customer_db",
      "expires_at": "2025-07-21T10:00:00Z"
    }
    ```
-   **Success Response (201 Created)**:
    ```json
    {
      "message": "Database access granted successfully",
      "access": {
        "id": "access-uuid",
        "database": "customer_db",
        "granted_by": "admin-uuid",
        "granted_at": "2025-06-21T10:00:00Z",
        "expires_at": "2025-07-21T10:00:00Z"
      }
    }
    ```

#### **Revoke Database Access**
-   **Endpoint**: `DELETE /api/users/<user_id>/database-access/<access_id>`
-   **Description**: Revokes a specific database access grant from a user.
-   **Authorization**: `Bearer <access_token>`
-   **Permissions**: `database_access.revoke`
-   **Success Response (200 OK)**:
    ```json
    {
      "message": "Database access revoked successfully"
    }
    ```

### Roles (`/api/roles`)

#### **Get All Roles**
-   **Endpoint**: `GET /api/roles`
-   **Description**: Retrieves all roles for the current organization.
-   **Authorization**: `Bearer <access_token>`
-   **Permissions**: `role.read`
-   **Success Response (200 OK)**:
    ```json
    {
      "roles": [
        { "id": "role-uuid-1", "name": "admin", ... },
        { "id": "role-uuid-2", "name": "viewer", ... }
      ]
    }
    ```

#### **Create a New Role**
-   **Endpoint**: `POST /api/roles`
-   **Description**: Creates a new role.
-   **Authorization**: `Bearer <access_token>`
-   **Permissions**: `role.create`
-   **Request Body**:
    ```json
    {
      "name": "support_agent",
      "display_name": "Support Agent",
      "description": "Handles customer support tickets.",
      "permissions": ["permission-uuid-1", "permission-uuid-2"]
    }
    ```
-   **Success Response (201 Created)**:
    ```json
    {
      "role": {
        "id": "new-role-uuid",
        "name": "support_agent",
        // ... includes permissions
      }
    }
    ```

### Audit (`/api/audit`)

#### **Get Audit Logs**
-   **Endpoint**: `GET /api/audit/logs`
-   **Description**: Retrieves audit logs, with optional filters.
-   **Authorization**: `Bearer <access_token>`
-   **Permissions**: `audit.read`
-   **Query Parameters**:
    -   `user_id` (string, optional)
    -   `action` (string, optional)
    -   `start_date` (ISO 8601 string, optional)
    -   `end_date` (ISO 8601 string, optional)
    -   `limit` (integer, optional, default: 100)
-   **Success Response (200 OK)**:
    ```json
    {
      "audit_logs": [
        {
          "id": "log-uuid",
          "user_id": "user-uuid",
          "action": "LOGIN",
          "ip_address": "127.0.0.1",
          "timestamp": "2023-10-27T10:00:00Z",
          ...
        }
      ],
      "count": 1
    }
    ```