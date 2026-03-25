# CertGuard — API_CONTRACT.md

## 1. Purpose
This document defines the HTTP API contract for the **CertGuard** project.

The API must remain:
- simple
- explicit
- strongly typed
- consistent
- easy to consume from the React frontend

All backend JSON fields must use `snake_case`.

---

## 2. Global API Rules

### 2.1 Base Path
```text
/api/v1
```

### 2.2 Content Type
All request and response bodies must use JSON unless the endpoint explicitly handles file upload.

- JSON: `application/json`
- File upload: `multipart/form-data`

### 2.3 Authentication
Authentication uses **JWT access token only**.

Protected endpoints must require:

```http
Authorization: Bearer <access_token>
```

When the token expires, the frontend must redirect the user to log in again.

### 2.4 Roles
Supported roles:
- `admin`
- `user`

Authorization rules:
- `admin`: full access
- `user`: read-only access

### 2.5 Response Envelope
All API responses must follow a standardized envelope.

#### Success response
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {}
}
```

#### Error response
```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": [
    {
      "field": "certificate",
      "detail": "Certificate is required."
    }
  ]
}
```

### 2.6 Error Shape
Each error item should follow:

```json
{
  "field": "string | null",
  "detail": "string"
}
```

Rules:
- `field` may be `null` for non-field-specific errors
- validation errors must be readable
- domain/business errors must return meaningful messages

### 2.7 Date and Time Format
Use ISO-like explicit string formats.

Recommended:
- Date: `YYYY-MM-DD`
- Time: `HH:MM`
- Datetime UTC: ISO 8601

Examples:
- `2026-04-30`
- `08:00`
- `2026-04-30T12:15:00Z`

### 2.8 Soft Delete Visibility
Soft-deleted records must not appear in normal list endpoints.

---

## 3. Shared DTOs

### 3.1 ErrorItem
```json
{
  "field": "string | null",
  "detail": "string"
}
```

### 3.2 StandardSuccessResponse
```json
{
  "success": true,
  "message": "string",
  "data": {}
}
```

### 3.3 StandardErrorResponse
```json
{
  "success": false,
  "message": "string",
  "errors": [
    {
      "field": "string | null",
      "detail": "string"
    }
  ]
}
```

### 3.4 Pagination
If pagination is introduced later, use this shape:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

The first implementation may remain simple without pagination if the dataset is small.

---

## 4. Authentication API

## 4.1 Login
### Endpoint
```http
POST /api/v1/auth/login
```

### Access
Public

### Request
```json
{
  "username": "admin",
  "password": "secret_password"
}
```

### Request DTO
`LoginRequest`
- `username: string`
- `password: string`

### Success Response
```json
{
  "success": true,
  "message": "Login completed successfully.",
  "data": {
    "access_token": "jwt_token",
    "token_type": "bearer",
    "expires_in_seconds": 900,
    "user": {
      "id": "c8c73f2f-7a9d-4b0f-9e0a-0e9c7d31a3d9",
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "is_active": true
    }
  }
}
```

### Response DTO
`LoginResponse`
- `access_token: string`
- `token_type: string`
- `expires_in_seconds: int`
- `user: AuthenticatedUserResponse`

### Notes
- Passwords must be hashed in storage.
- The API must not expose password hashes.

---

## 4.2 Get Current User
### Endpoint
```http
GET /api/v1/auth/me
```

### Access
Authenticated user

### Success Response
```json
{
  "success": true,
  "message": "Current user retrieved successfully.",
  "data": {
    "id": "c8c73f2f-7a9d-4b0f-9e0a-0e9c7d31a3d9",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true
  }
}
```

### Response DTO
`AuthenticatedUserResponse`
- `id: uuid string`
- `username: string`
- `email: string`
- `role: string`
- `is_active: bool`

---

## 4.3 Logout
### Endpoint
```http
POST /api/v1/auth/logout
```

### Access
Authenticated user

### Request
No body required.

### Success Response
```json
{
  "success": true,
  "message": "Logout completed successfully.",
  "data": null
}
```

### Notes
- Since the app uses access token only, logout may be handled as a client-side session clear plus optional audit logging.

---

## 5. Users API

## 5.1 Create User
### Endpoint
```http
POST /api/v1/users
```

### Access
Admin only

### Request
```json
{
  "username": "john_admin",
  "email": "john@example.com",
  "password": "secret_password",
  "role": "admin",
  "is_active": true
}
```

### Request DTO
`CreateUserRequest`
- `username: string`
- `email: string`
- `password: string`
- `role: "admin" | "user"`
- `is_active: bool`

### Success Response
```json
{
  "success": true,
  "message": "User created successfully.",
  "data": {
    "id": "b0a0b0e3-15f1-4ddf-9a5f-8abf6e6c8b10",
    "username": "john_admin",
    "email": "john@example.com",
    "role": "admin",
    "is_active": true,
    "created_at": "2026-03-23T12:00:00Z",
    "updated_at": "2026-03-23T12:00:00Z"
  }
}
```

### Response DTO
`UserResponse`
- `id: uuid string`
- `username: string`
- `email: string`
- `role: string`
- `is_active: bool`
- `created_at: datetime string`
- `updated_at: datetime string`

---

## 5.2 List Users
### Endpoint
```http
GET /api/v1/users
```

### Access
Admin only

### Success Response
```json
{
  "success": true,
  "message": "Users retrieved successfully.",
  "data": [
    {
      "id": "c8c73f2f-7a9d-4b0f-9e0a-0e9c7d31a3d9",
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "is_active": true,
      "created_at": "2026-03-23T12:00:00Z",
      "updated_at": "2026-03-23T12:00:00Z"
    }
  ]
}
```

---

## 5.3 Get User by ID
### Endpoint
```http
GET /api/v1/users/{user_id}
```

### Access
Admin only

### Path Parameters
- `user_id: uuid string`

---

## 5.4 Update User
### Endpoint
```http
PUT /api/v1/users/{user_id}
```

### Access
Admin only

### Request
```json
{
  "username": "john_admin",
  "email": "john.updated@example.com",
  "role": "user",
  "is_active": true
}
```

### Request DTO
`UpdateUserRequest`
- `username: string`
- `email: string`
- `role: "admin" | "user"`
- `is_active: bool`

---

## 5.5 Change User Password
### Endpoint
```http
PUT /api/v1/users/{user_id}/password
```

### Access
Admin only

### Request
```json
{
  "new_password": "new_secret_password"
}
```

### Request DTO
`ChangeUserPasswordRequest`
- `new_password: string`

---

## 5.6 Delete User
### Endpoint
```http
DELETE /api/v1/users/{user_id}
```

### Access
Admin only

### Behavior
Soft delete only.

### Success Response
```json
{
  "success": true,
  "message": "User deleted successfully.",
  "data": null
}
```

---

## 6. Certificates API

## 6.1 Create Certificate
### Endpoint
```http
POST /api/v1/certificates
```

### Access
Admin only

### Request
```json
{
  "certificate": "OBR Web API Certificate",
  "security_token_value": "1234567890",
  "used_by": "OBR API",
  "environment": "prod",
  "expiration_date": "2026-05-01"
}
```

### Request DTO
`CreateCertificateRequest`
- `certificate: string`
- `security_token_value: string`
- `used_by: string`
- `environment: string`
- `expiration_date: string`

### Success Response
```json
{
  "success": true,
  "message": "Certificate created successfully.",
  "data": {
    "id": 1,
    "certificate": "OBR Web API Certificate",
    "security_token_value": "1234567890",
    "used_by": "OBR API",
    "environment": "prod",
    "expiration_date": "2026-05-01",
    "created_at": "2026-03-23T12:00:00Z",
    "updated_at": "2026-03-23T12:00:00Z"
  }
}
```

### Response DTO
`CertificateResponse`
- `id: int`
- `certificate: string`
- `security_token_value: string`
- `used_by: string`
- `environment: string`
- `expiration_date: string`
- `created_at: datetime string`
- `updated_at: datetime string`

---

## 6.2 List Certificates
### Endpoint
```http
GET /api/v1/certificates
```

### Access
Authenticated user

### Optional Query Parameters
- `search: string`
- `environment: string`
- `expiring_within_days: int`

### Success Response
```json
{
  "success": true,
  "message": "Certificates retrieved successfully.",
  "data": [
    {
      "id": 1,
      "certificate": "OBR Web API Certificate",
      "security_token_value": "1234567890",
      "used_by": "OBR API",
      "environment": "prod",
      "expiration_date": "2026-05-01",
      "created_at": "2026-03-23T12:00:00Z",
      "updated_at": "2026-03-23T12:00:00Z"
    }
  ]
}
```

---

## 6.3 Get Certificate by ID
### Endpoint
```http
GET /api/v1/certificates/{certificate_id}
```

### Access
Authenticated user

### Path Parameters
- `certificate_id: int`

---

## 6.4 Update Certificate
### Endpoint
```http
PUT /api/v1/certificates/{certificate_id}
```

### Access
Admin only

### Request
```json
{
  "certificate": "OBR Web API Certificate",
  "security_token_value": "1234567890_UPDATED",
  "used_by": "OBR API",
  "environment": "uat",
  "expiration_date": "2026-06-01"
}
```

### Request DTO
`UpdateCertificateRequest`
- `certificate: string`
- `security_token_value: string`
- `used_by: string`
- `environment: string`
- `expiration_date: string`

---

## 6.5 Delete Certificate
### Endpoint
```http
DELETE /api/v1/certificates/{certificate_id}
```

### Access
Admin only

### Behavior
Soft delete only.

### Success Response
```json
{
  "success": true,
  "message": "Certificate deleted successfully.",
  "data": null
}
```

---

## 6.6 Certificate Import Preview
### Endpoint
```http
POST /api/v1/certificates/import/preview
```

### Access
Admin only

### Content Type
`multipart/form-data`

### Form Data
- `file: UploadFile`

### Behavior
The backend must:
- validate the uploaded Excel file
- trim spaces
- ignore fully blank rows
- remove duplicates inside the file using `certificate`
- compare rows against the database
- classify rows as `insert` or `update`
- return a preview summary

### Success Response
```json
{
  "success": true,
  "message": "Import preview generated successfully.",
  "data": {
    "total_rows": 10,
    "valid_rows": 8,
    "insert_count": 5,
    "update_count": 3,
    "skipped_count": 2,
    "errors": [
      {
        "row_number": 7,
        "detail": "Expiration date is required."
      }
    ],
    "preview_items": [
      {
        "row_number": 1,
        "certificate": "OBR API Cert",
        "security_token_value": "ABC123",
        "used_by": "OBR API",
        "environment": "prod",
        "expiration_date": "2026-05-01",
        "action": "insert"
      },
      {
        "row_number": 2,
        "certificate": "OBR UI Cert",
        "security_token_value": "XYZ999",
        "used_by": "OBR UI",
        "environment": "uat",
        "expiration_date": "2026-06-01",
        "action": "update"
      }
    ]
  }
}
```

### Response DTO
`ImportCertificatesPreviewResponse`
- `total_rows: int`
- `valid_rows: int`
- `insert_count: int`
- `update_count: int`
- `skipped_count: int`
- `errors: list[ImportRowErrorResponse]`
- `preview_items: list[ImportPreviewItemResponse]`

### Preview item DTO
`ImportPreviewItemResponse`
- `row_number: int`
- `certificate: string`
- `security_token_value: string`
- `used_by: string`
- `environment: string`
- `expiration_date: string`
- `action: "insert" | "update"`

---

## 6.7 Certificate Import Confirm
### Endpoint
```http
POST /api/v1/certificates/import/confirm
```

### Access
Admin only

### Request
The frontend should send the cleaned preview payload or a temporary import token, depending on the implementation choice.

### Recommended simple request
```json
{
  "items": [
    {
      "certificate": "OBR API Cert",
      "security_token_value": "ABC123",
      "used_by": "OBR API",
      "environment": "prod",
      "expiration_date": "2026-05-01"
    }
  ]
}
```

### Required backend rule
The backend must revalidate the data before persistence and must not trust client-side preview state alone.

### Success Response
```json
{
  "success": true,
  "message": "Certificates imported successfully.",
  "data": {
    "insert_count": 5,
    "update_count": 3,
    "skipped_count": 0,
    "errors": [
      {
        "row_number": 2,
        "detail": "Expiration date is required."
      }
    ]
  }
}
```

### Response DTO
`ConfirmCertificatesImportResponse`
- `insert_count: int`
- `update_count: int`
- `skipped_count: int`
- `errors: list[ImportRowErrorResponse]`

---

## 7. Notification Settings API

## 7.1 Get Notification Settings
### Endpoint
```http
GET /api/v1/notifications/settings
```

### Access
Admin only

### Success Response
```json
{
  "success": true,
  "message": "Notification settings retrieved successfully.",
  "data": {
    "enabled": true,
    "recipient_emails": [
      "ops@example.com",
      "admin@example.com"
    ],
    "days_before_expiration": 30,
    "send_time": "08:00",
    "send_days": [
      "monday",
      "tuesday",
      "wednesday",
      "thursday",
      "friday"
    ],
    "from_email": "noreply@example.com",
    "subject_template": "Certificates expiring soon - {process_date}",
    "body_template": "The following certificates are close to expiration.",
    "attachment_file_name_template": "certificates_expiring_{process_date}.csv"
  }
}
```

### Response DTO
`NotificationSettingsResponse`
- `enabled: bool`
- `recipient_emails: list[string]`
- `days_before_expiration: int`
- `send_time: string`
- `send_days: list[string]`
- `from_email: string`
- `subject_template: string`
- `body_template: string`
- `attachment_file_name_template: string | null`

---

## 7.2 Update Notification Settings
### Endpoint
```http
PUT /api/v1/notifications/settings
```

### Access
Admin only

### Request
```json
{
  "enabled": true,
  "recipient_emails": [
    "ops@example.com",
    "admin@example.com"
  ],
  "days_before_expiration": 30,
  "send_time": "08:00",
  "send_days": [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday"
  ],
  "from_email": "noreply@example.com",
  "subject_template": "Certificates expiring soon - {process_date}",
  "body_template": "The following certificates are close to expiration.",
  "attachment_file_name_template": "certificates_expiring_{process_date}.csv"
}
```

### Request DTO
`UpdateNotificationSettingsRequest`
- `enabled: bool`
- `recipient_emails: list[string]`
- `days_before_expiration: int`
- `send_time: string`
- `send_days: list[string]`
- `from_email: string`
- `subject_template: string`
- `body_template: string`
- `attachment_file_name_template: string | null`

---

## 7.3 Send Test Notification
### Endpoint
```http
POST /api/v1/notifications/test
```

### Access
Admin only

### Purpose
Send a test email using the current notification settings and template.

### Success Response
```json
{
  "success": true,
  "message": "Test notification sent successfully.",
  "data": null
}
```

### Notes
This endpoint is useful for validating SMTP configuration and template rendering.

---

## 7.4 Send Notification Now
### Endpoint
```http
POST /api/v1/notifications/send
```

### Access
Admin only

### Purpose
Trigger the real notification send flow manually (same behavior as the scheduled job).

### Success Response
```json
{
  "success": true,
  "message": "Notification sent successfully.",
  "data": null
}
```

---

## 8. Dashboard API

## 8.1 Get Dashboard Summary
### Endpoint
```http
GET /api/v1/dashboard/summary
```

### Access
Authenticated user

### Success Response
```json
{
  "success": true,
  "message": "Dashboard summary retrieved successfully.",
  "data": {
    "total_certificates": 25,
    "expiring_soon_certificates": 4,
    "active_users": 2
  }
}
```

### Response DTO
`DashboardSummaryResponse`
- `total_certificates: int`
- `expiring_soon_certificates: int`
- `active_users: int`

---

## 9. Transaction Logs API

## 9.1 List Transaction Logs
### Endpoint
```http
GET /api/v1/logs/transactions
```

### Access
Admin only

### Optional Query Parameters
- `action_type: string`
- `entity_domain: string`
- `modified_by: string`
- `date_from: string`
- `date_to: string`

### Success Response
```json
{
  "success": true,
  "message": "Transaction logs retrieved successfully.",
  "data": [
    {
      "transaction_uid": "f6a54d57-2b7c-4f5a-b1b3-abc123xyz000",
      "action_type": "update_certificate",
      "transaction_date": "2026-03-23T08:00:00",
      "transaction_date_utc": "2026-03-23T12:00:00Z",
      "modified_by": "admin",
      "details": [
        {
          "uid": 1,
          "entity_domain": "certificate",
          "entity_id": "5",
          "transaction_description": "Updated certificate expiration date.",
          "changes": {
            "before": {
              "expiration_date": "2026-05-01"
            },
            "after": {
              "expiration_date": "2026-06-01"
            }
          }
        }
      ]
    }
  ]
}
```

### Response DTO
`TransactionLogResponse`
- `transaction_uid: string`
- `action_type: string`
- `transaction_date: datetime string`
- `transaction_date_utc: datetime string`
- `modified_by: string`
- `details: list[TransactionLogDetailResponse]`

### Detail DTO
`TransactionLogDetailResponse`
- `uid: int`
- `entity_domain: string`
- `entity_id: string`
- `transaction_description: string`
- `changes: object | null`

---

## 10. Health API

## 10.1 Health Check
### Endpoint
```http
GET /api/v1/health
```

### Access
Public

### Success Response
```json
{
  "success": true,
  "message": "Health check completed successfully.",
  "data": {
    "status": "ok",
    "app_name": "CertGuard"
  }
}
```

---

## 11. Validation Rules

### 11.1 User Validation
- `username` is required
- `email` must be valid
- `password` is required on create
- `role` must be `admin` or `user`

### 11.2 Certificate Validation
- `certificate` is required
- `certificate` must be unique
- `expiration_date` is required
- all other fields may be plain text but should still be trimmed

### 11.3 Notification Validation
- `recipient_emails` must contain valid emails
- `days_before_expiration` must be greater than or equal to 1
- `send_time` must follow `HH:MM`
- `send_days` must use allowed weekday names
- templates must only support approved placeholders

### 11.4 Import Validation
Expected Excel columns:
- `Certificate`
- `Security token value (Serial number)`
- `Used by`
- `Environments`
- `Expiration date`

The importer must normalize these columns into internal API field names:
- `certificate`
- `security_token_value`
- `used_by`
- `environment`
- `expiration_date`

---

## 12. Authorization Matrix

| Endpoint Group | Admin | User |
|---|---:|---:|
| auth/me | yes | yes |
| users | yes | no |
| certificates list/get | yes | yes |
| certificates create/update/delete | yes | no |
| certificates import | yes | no |
| notification settings | yes | no |
| dashboard summary | yes | yes |
| transaction logs | yes | no |
| health | yes | yes |

---

## 13. Placeholder Rules for Email Templates

Allowed placeholders should remain limited and explicit.

Recommended placeholders:
- `{process_date}`
- `{days_before_expiration}`
- `{expiring_certificates_count}`

If certificate details need to appear in the email body, the backend should render them as a generated section rather than allowing arbitrary template logic.

Do not build a full template engine.

---

## 14. Versioning Rules
The first API version is:

```text
v1
```

All initial endpoints must live under `/api/v1`.

If future breaking changes are introduced, create a new versioned path instead of silently changing existing contracts.

---

## 15. Final API Rule
The CertGuard API must feel:
- explicit
- predictable
- easy to consume
- consistent across modules

It must not feel:
- improvised
- inconsistent
- overengineered
