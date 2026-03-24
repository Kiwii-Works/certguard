# CertGuard — skills.md

## 1. Purpose
This document defines the engineering rules, architecture boundaries, and coding standards for the CertGuard project.

CertGuard is a small internal administrative application used to manage certificates, track expiration dates, import certificate data from Excel files, and send configurable email notifications for certificates that are close to expiration.

The project must remain:
- simple
- maintainable
- strongly typed
- readable
- reusable where reasonable
- easy to evolve without overengineering

---

## 2. Approved Technology Stack

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- APScheduler
- pytest
- Ruff
- mypy

### Frontend
- React
- Vite
- TypeScript
- ESLint
- Prettier

---

## 3. Project Philosophy

### Simplicity First
Favor clarity over complexity.

### Clean Boundaries
- Routes → HTTP only
- Services → business logic
- Repositories → DB access
- Schemas → API contracts
- Models → persistence

### Strong Typing Mandatory
No untyped logic.

---

## 4. Functional Scope
Modules:
1. Authentication
2. Users
3. Certificates
4. Excel Import
5. Notification Settings
6. Email Templates
7. Dashboard
8. Transaction Logs

---

## 5. Domain Rules

### Certificate
- certificate (unique)
- security_token_value
- used_by (text)
- environment (text)
- expiration_date

### Excel Import
- trim spaces
- ignore empty rows
- deduplicate by certificate
- insert or update
- preview must show insert/update

### Notifications
Global config:
- enabled
- recipient_emails
- days_before_expiration
- send_time
- send_days
- from_email
- subject_template
- body_template

### Auth
- JWT only
- no refresh token
- roles: admin / user

### Logs
Track:
- login/logout
- CRUD users
- CRUD certificates
- import
- notification updates

---

## 6. Backend Structure

backend/
  app/
    core/
    modules/
    shared/

Modules:
- auth
- users
- certificates
- notifications
- dashboard
- logs

Each module:
- router.py
- schemas.py
- service.py
- repository.py
- models.py

---

## 7. API Rules

### Response format
Success:
{ "success": true, "data": {} }

Error:
{ "success": false, "message": "", "errors": [] }

### Naming
- snake_case in backend JSON

---

## 8. Database

- SQLite
- certificate unique
- soft delete:
  - users
  - certificates

---

## 9. Scheduler

- APScheduler only
- runs daily checks
- sends grouped emails

---

## 10. Frontend

Structure:
- api/
- pages/
- components/
- dto/

Pages:
- Login
- Dashboard
- Certificates
- Import
- Users
- Notifications
- Logs

---

## 11. Naming Conventions

Python:
- snake_case
- PascalCase classes

TypeScript:
- PascalCase components
- strict typing

---

## 12. Code Quality

Do NOT:
- business logic in routes
- DB access in routes
- mix schemas and models
- use Any

---

## 13. Testing

Must cover:
- auth
- certificate CRUD
- import logic
- notifications

---

## 14. Linting

Backend:
- Ruff
- mypy

Frontend:
- ESLint
- Prettier
- TS strict

---

## 15. Dashboard

- total certificates
- expiring soon
- active users

---

## 16. Copilot Rules

- follow structure
- do not invent patterns
- keep it simple
- keep typing strict

---

## Final Rule

CertGuard must feel:
- clean
- professional
- simple
