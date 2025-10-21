"""Retrofit existing AuditTrail.detail values to include user names for entries
that were recorded before enhanced formatting.

Run: python retrofit_audit_names.py
"""
from app import create_app, db
from app.models import AuditTrail, User

app = create_app()

KEY_WORDS = ['Assigned to employee', 'Submitted to manager', 'Manager approved submission', 'Manager rejected submission', 'Auditor closed query', 'Auditor reopened query', 'File', 'Comment added']

def needs_update(detail: str) -> bool:
    # If detail already has a closing parenthesis after ID or contains fullname, skip
    return not (')' in detail and 'ID' in detail) and any(k in detail for k in KEY_WORDS)

with app.app_context():
    updates = 0
    for entry in AuditTrail.query.all():
        if entry.user_id and needs_update(entry.detail or ''):
            user = User.query.get(entry.user_id)
            if user:
                # Append name info
                entry.detail = f"{entry.detail} by (ID {user.id}) {user.full_name or user.username}".strip()
                updates += 1
    if updates:
        db.session.commit()
    print(f"Retrofit complete. Updated {updates} audit trail rows.")