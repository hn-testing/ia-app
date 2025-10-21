# Internal Audit App

A simple internal auditing workflow application for a bank built with Flask and PostgreSQL.

## Features
- Role-based users: Auditor, Employee, Manager
- Auditor can create queries selecting Category/SubCategory, choose template and/or custom text
- Auditor can assign query to Employee
- Employee submits response selecting Manager, uploading files
- Manager approves or rejects; rejection loops back to Employee
- Auditor closes or reopens (reopen loops workflow)
- Comments by any user anytime
- Audit trail for all actions & comments
- File attachments tracked and downloadable
- Basic notifications badge for pending tasks

## Tech Stack
- Python Flask
- PostgreSQL (`test_ia_app1`)
- SQLAlchemy ORM, Flask-Migrate (migrations future-ready)
- Bootstrap 5 for UI

## Setup

### 1. Create database
Ensure PostgreSQL is running and create database:
```sql
CREATE DATABASE test_ia_app1;
```

### 2. Environment
Copy `.env` (already present) and adjust if needed:
```
SECRET_KEY=change-me
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/test_ia_app1
UPLOAD_FOLDER=app/uploads
```

### 3. Install dependencies
Activate your virtual environment `.venv` then install:
```bash
pip install -r requirements.txt
```

### 4. Seed data
```bash
# only first time, later use only seed.py
python -m flask db init    # only if migrations folder does not exist yet
python -m flask db migrate -m "Add target_user_id to audit_trail"
python -m flask db upgrade
```
```bash
python seed.py
```
Creates sample users (auditor1 / employee1 / manager1 all with password `password`), categories, subcategories, and templates.

### 5. Run app
```bash
python run.py
```
Visit: http://127.0.0.1:5000/login

### 6. Login credentials
- Auditor: auditor1 / password
- Employee: employee1 / password
- Manager: manager1 / password
- auditor1
auditor2
auditor3
employee1
employee2
employee3
employee4
employee5
manager1
manager2

## Workflow Summary
1. Auditor creates query (optionally assigns employee immediately) -> status `assigned` or `draft`.
2. Employee uploads files & selects manager -> status `employee_submitted`.
3. Manager decision -> `manager_approved` or `manager_rejected`.
4. Auditor closes (`closed`) or reopens (`reopened`). Reopen allows employee submission again.

## Future Improvements
- Proper WTForms & validation
- Email notifications
- More granular permissions
- Pagination & search
- Migrations with `flask db init/migrate/upgrade`
- Unit tests expansion

## Tests
Placeholder test suite to be added under `tests/`.

