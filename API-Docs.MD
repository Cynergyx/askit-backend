# Cynergyx-Askit API Documentation

> API collection for the Cynergyx-Askit backend application.

**Base URL:** `{{baseUrl}}`

> Use the `{{jwt}}` token obtained from login for all authenticated requests.

---

## 🔐 Auth

### Login

**POST** `/api/auth/login`

Authenticate a user and receive a JWT token.

**Request Body:**

```json
{
  "email": "admin@innovatecorp.com",
  "password": "StrongPassword123!",
  "organization": "innovatecorp.com"
}
```

**Response:**
Returns `access_token`, `user.id`, and `user.organization_id`.

---

### Register New User

**POST** `/api/auth/register`

Registers a new user under an existing organization.

**Request Body:**

```json
{
  "email": "new.user@innovatecorp.com",
  "password": "VeryStrongPassword123!",
  "first_name": "New",
  "last_name": "User",
  "organization": "innovatecorp.com"
}
```

---

### Logout

**POST** `/api/auth/logout`

Logs out the current authenticated user.

---

## 🏢 Organization

### Onboard New Organization

**POST** `/api/organizations/onboard`

> Requires Super Admin JWT

Creates a new organization, sets roles and creates users.

**Request Body:**

```json
{
  "organization": {
    "name": "Innovate Corp",
    "domain": "innovatecorp.com"
  },
  "roles": [
    { "name": "Data Analyst", "description": "Can view dashboards and run queries." },
    { "name": "Project Manager", "description": "Manages projects and users." }
  ],
  "users": [
    {
      "email": "admin@innovatecorp.com",
      "password": "StrongPassword123!",
      "first_name": "Org",
      "last_name": "Admin",
      "is_admin": true
    },
    {
      "email": "analyst@innovatecorp.com",
      "password": "AnotherPassword456!",
      "first_name": "Data",
      "last_name": "Person",
      "is_admin": false,
      "roles": ["Data Analyst"]
    }
  ]
}
```

---

## 👤 Users

### Get All Users

**GET** `/api/users?search=admin`

Search and retrieve users.

---

### Create User

**POST** `/api/users`

**Request Body:**

```json
{
  "email": "new.hire@innovatecorp.com",
  "first_name": "New",
  "last_name": "Hire",
  "password": "DefaultPassword123!"
}
```

---

### Get User by ID

**GET** `/api/users/{{user_id}}`

Retrieve user details.

---

## 🛡️ Roles & Permissions

### Get All Roles

**GET** `/api/roles`

Lists all defined roles in the organization.

---

### Assign Role to User

**POST** `/api/users/{{user_id}}/roles`

**Request Body:**

```json
{
  "role_id": "<role_id_to_assign>"
}
```

---

### Revoke Role from User

**DELETE** `/api/users/{{user_id}}/roles`

**Request Body:**

```json
{
  "role_id": "<role_id_to_revoke>"
}
```

---

## 📝 Role Requests

### User Requests a Role

**POST** `/api/role-requests`

**Request Body:**

```json
{
  "role_id": "<desired_role_id>",
  "reason": "I need access to the Data Analyst tools to complete my Q3 report."
}
```

---

### Admin Lists Pending Requests

**GET** `/api/role-requests?status=PENDING`

---

### Admin Approves Request

**POST** `/api/role-requests/<request_id>/approve`

**Request Body:**

```json
{
  "notes": "Approved for Q3 reporting needs. Access will be reviewed in 90 days."
}
```

---

## 💾 Data Sources & Access

### Bulk Upload Data Sources

**POST** `/api/datasources/bulk-upload`

**Request Body:**

```json
[
  {
    "name": "Production Postgres DB",
    "type": "postgresql",
    "host": "prod.db.innovatecorp.com",
    "port": 5432,
    "database_name": "sales",
    "username": "readonly_user",
    "password": "ThisWillBeEncrypted"
  }
]
```

---

### Grant DB Access to User

**POST** `/api/users/{{user_id}}/database-access`

**Request Body:**

```json
{
  "data_source_id": "{{data_source_id}}"
}
```

---

## 💬 Chat & AI

### Create Chat Session

**POST** `/api/chat/sessions`

**Request Body:**

```json
{
  "title": "Q3 Product Sales Analysis"
}
```

---

### Post Message to AI

**POST** `/api/chat/sessions/{{session_id}}/messages`

**Request Body:**

```json
{
  "query": "Show me the top 5 selling products last month."
}
```

---

### Get Chat History

**GET** `/api/chat/sessions/{{session_id}}/messages`

---

## 🧾 Audit

### Get Audit Logs

**GET** `/api/audit/logs?limit=10`

---