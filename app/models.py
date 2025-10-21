from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from . import db, login_manager

class QueryStatus(Enum):
    DRAFT = 'draft'
    ASSIGNED = 'assigned'
    EMPLOYEE_SUBMITTED = 'employee_submitted'
    MANAGER_APPROVED = 'manager_approved'
    MANAGER_REJECTED = 'manager_rejected'
    CLOSED = 'closed'
    REOPENED = 'reopened'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False)  # auditor, employee, manager
    full_name = db.Column(db.String(120))
    email = db.Column(db.String(120))

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    subcategories = db.relationship('SubCategory', backref='category', lazy=True)

class SubCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

class QueryTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('sub_category.id'), nullable=True)
    text = db.Column(db.Text, nullable=False)

class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('sub_category.id'), nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey('query_template.id'), nullable=True)
    custom_text = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(40), nullable=False, default=QueryStatus.DRAFT.value)
    auditor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    auditor = db.relationship('User', foreign_keys=[auditor_id])
    assigned_employee = db.relationship('User', foreign_keys=[assigned_employee_id])
    manager = db.relationship('User', foreign_keys=[manager_id])
    category = db.relationship('Category')
    subcategory = db.relationship('SubCategory')
    template = db.relationship('QueryTemplate')
    category = db.relationship('Category')
    subcategory = db.relationship('SubCategory')
    template = db.relationship('QueryTemplate')

    comments = db.relationship('Comment', backref='query', lazy=True, cascade='all, delete-orphan')
    attachments = db.relationship('Attachment', backref='query', lazy=True, cascade='all, delete-orphan')
    audit_trail_entries = db.relationship('AuditTrail', backref='query', lazy=True, cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255))
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploaded_by = db.relationship('User')

class AuditTrail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query.id'), nullable=False)
    action = db.Column(db.String(120), nullable=False)
    detail = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    target_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # user impacted by the action (e.g., assigned employee, manager)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
    target_user = db.relationship('User', foreign_keys=[target_user_id])

# Utility functions

def record_audit_action(query, action, detail, user_id=None, target_user_id=None):
    entry = AuditTrail(query=query, action=action, detail=detail, user_id=user_id, target_user_id=target_user_id)
    db.session.add(entry)

