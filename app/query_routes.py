from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import db, allowed_file
from .models import Category, SubCategory, QueryTemplate, Query, User, Comment, Attachment, record_audit_action, QueryStatus

query_bp = Blueprint('query', __name__)

@query_bp.route('/')
@login_required
def dashboard():
    # Basic segregation by role
    if current_user.role == 'auditor':
        queries = Query.query.filter_by(auditor_id=current_user.id).all()
    elif current_user.role == 'employee':
        queries = Query.query.filter_by(assigned_employee_id=current_user.id).all()
    elif current_user.role == 'manager':
        queries = Query.query.filter_by(manager_id=current_user.id).all()
    else:
        queries = []
    return render_template('dashboard.html', queries=queries)

@query_bp.route('/query/new', methods=['GET','POST'])
@login_required
def new_query():
    if current_user.role != 'auditor':
        flash('Only auditors can create queries', 'warning')
        return redirect(url_for('query.dashboard'))
    categories = Category.query.all()
    templates = QueryTemplate.query.all()
    employees = User.query.filter_by(role='employee').all()
    if request.method == 'POST':
        category_id = request.form.get('category')
        subcategory_id = request.form.get('subcategory') or None
        template_id = request.form.get('template') or None
        custom_text = request.form.get('custom_text') or None
        assigned_employee_id = request.form.get('assigned_employee') or None
        q = Query(category_id=category_id, subcategory_id=subcategory_id, template_id=template_id,
                  custom_text=custom_text, auditor_id=current_user.id,
                  assigned_employee_id=assigned_employee_id,
                  status=QueryStatus.ASSIGNED.value if assigned_employee_id else QueryStatus.DRAFT.value)
        db.session.add(q)
        db.session.flush()
        record_audit_action(q, 'created', f'Query created by auditor (ID {current_user.id}) {current_user.full_name or current_user.username}', user_id=current_user.id)
        if assigned_employee_id:
            emp = User.query.get(int(assigned_employee_id))
            if emp:
                record_audit_action(q, 'assigned', f'Assigned to employee (ID {emp.id}) {emp.full_name or emp.username}', user_id=current_user.id, target_user_id=emp.id)
        # handle files
        for f in request.files.getlist('attachments'):
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                save_path = current_app.config['UPLOAD_FOLDER']
                f.save(f"{save_path}/{q.id}_{filename}")
                att = Attachment(query_id=q.id, filename=f"{q.id}_{filename}", original_name=filename, uploaded_by_id=current_user.id)
                db.session.add(att)
                record_audit_action(q, 'file_upload', f'File {filename} uploaded by (ID {current_user.id}) {current_user.full_name or current_user.username}', user_id=current_user.id)
        db.session.commit()
        flash('Query created', 'success')
        return redirect(url_for('query.dashboard'))
    return render_template('new_query.html', categories=categories, templates=templates, employees=employees)

@query_bp.route('/subcategories/<int:category_id>')
@login_required
def get_subcategories(category_id):
    subs = SubCategory.query.filter_by(category_id=category_id).all()
    return jsonify([{'id': s.id, 'name': s.name} for s in subs])

@query_bp.route('/query/<int:query_id>')
@login_required
def view_query(query_id):
    q = Query.query.get_or_404(query_id)
    audit_trail = q.audit_trail_entries
    comments = q.comments
    employees = User.query.filter_by(role='employee').all()
    managers = User.query.filter_by(role='manager').all()
    return render_template('query_detail.html', q=q, audit_trail=audit_trail, comments=comments, employees=employees, managers=managers)

@query_bp.route('/query/<int:query_id>/assign', methods=['POST'])
@login_required
def assign_employee(query_id):
    q = Query.query.get_or_404(query_id)
    if current_user.role != 'auditor':
        flash('Only auditor can assign employee', 'warning')
        return redirect(url_for('query.view_query', query_id=query_id))
    emp_id = request.form.get('assigned_employee')
    if emp_id:
        q.assigned_employee_id = emp_id
        q.status = QueryStatus.ASSIGNED.value
        emp = User.query.get(int(emp_id))
        if emp:
            record_audit_action(q, 'assigned', f'Assigned to employee (ID {emp.id}) {emp.full_name or emp.username}', user_id=current_user.id, target_user_id=emp.id)
        db.session.commit()
        flash('Employee assigned', 'success')
    return redirect(url_for('query.view_query', query_id=query_id))

@query_bp.route('/query/<int:query_id>/employee_submit', methods=['POST'])
@login_required
def employee_submit(query_id):
    q = Query.query.get_or_404(query_id)
    if current_user.role != 'employee' or q.assigned_employee_id != current_user.id:
        flash('Not authorized', 'danger')
        return redirect(url_for('query.view_query', query_id=query_id))
    manager_id = request.form.get('manager_id')
    q.manager_id = manager_id
    q.status = QueryStatus.EMPLOYEE_SUBMITTED.value
    mgr = User.query.get(int(manager_id)) if manager_id else None
    if mgr:
        record_audit_action(q, 'employee_submitted', f'Submitted to manager (ID {mgr.id}) {mgr.full_name or mgr.username}', user_id=current_user.id, target_user_id=mgr.id)
    else:
        record_audit_action(q, 'employee_submitted', 'Submitted to manager (ID unknown)', user_id=current_user.id)
    for f in request.files.getlist('attachments'):
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            save_path = current_app.config['UPLOAD_FOLDER']
            f.save(f"{save_path}/{q.id}_{filename}")
            att = Attachment(query_id=q.id, filename=f"{q.id}_{filename}", original_name=filename, uploaded_by_id=current_user.id)
            db.session.add(att)
            record_audit_action(q, 'file_upload', f'File {filename} uploaded by (ID {current_user.id}) {current_user.full_name or current_user.username}', user_id=current_user.id)
    db.session.commit()
    flash('Submitted to manager', 'success')
    return redirect(url_for('query.view_query', query_id=query_id))

@query_bp.route('/query/<int:query_id>/manager_decide', methods=['POST'])
@login_required
def manager_decide(query_id):
    q = Query.query.get_or_404(query_id)
    if current_user.role != 'manager' or q.manager_id != current_user.id:
        flash('Not authorized', 'danger')
        return redirect(url_for('query.view_query', query_id=query_id))
    decision = request.form.get('decision')
    if decision == 'approve':
        q.status = QueryStatus.MANAGER_APPROVED.value
        record_audit_action(q, 'manager_approved', f'Manager (ID {current_user.id}) {current_user.full_name or current_user.username} approved submission', user_id=current_user.id, target_user_id=q.assigned_employee_id)
    else:
        q.status = QueryStatus.MANAGER_REJECTED.value
        record_audit_action(q, 'manager_rejected', f'Manager (ID {current_user.id}) {current_user.full_name or current_user.username} rejected submission', user_id=current_user.id, target_user_id=q.assigned_employee_id)
    db.session.commit()
    flash('Manager decision recorded', 'success')
    return redirect(url_for('query.view_query', query_id=query_id))

@query_bp.route('/query/<int:query_id>/auditor_close', methods=['POST'])
@login_required
def auditor_close(query_id):
    q = Query.query.get_or_404(query_id)
    if current_user.role != 'auditor' or q.auditor_id != current_user.id:
        flash('Not authorized', 'danger')
        return redirect(url_for('query.view_query', query_id=query_id))
    q.status = QueryStatus.CLOSED.value
    record_audit_action(q, 'closed', f'Auditor (ID {current_user.id}) {current_user.full_name or current_user.username} closed query', user_id=current_user.id, target_user_id=q.assigned_employee_id)
    db.session.commit()
    flash('Query closed', 'success')
    return redirect(url_for('query.view_query', query_id=query_id))

@query_bp.route('/query/<int:query_id>/auditor_reopen', methods=['POST'])
@login_required
def auditor_reopen(query_id):
    q = Query.query.get_or_404(query_id)
    if current_user.role != 'auditor' or q.auditor_id != current_user.id:
        flash('Not authorized', 'danger')
        return redirect(url_for('query.view_query', query_id=query_id))
    q.status = QueryStatus.REOPENED.value
    record_audit_action(q, 'reopened', f'Auditor (ID {current_user.id}) {current_user.full_name or current_user.username} reopened query', user_id=current_user.id, target_user_id=q.assigned_employee_id)
    db.session.commit()
    flash('Query reopened', 'success')
    return redirect(url_for('query.view_query', query_id=query_id))

@query_bp.route('/query/<int:query_id>/comment', methods=['POST'])
@login_required
def add_comment(query_id):
    q = Query.query.get_or_404(query_id)
    content = request.form.get('comment')
    if content:
        c = Comment(query_id=query_id, user_id=current_user.id, content=content)
        db.session.add(c)
        record_audit_action(q, 'comment', f'Comment added by (ID {current_user.id}) {current_user.full_name or current_user.username}', user_id=current_user.id)
        db.session.commit()
        flash('Comment added', 'success')
    return redirect(url_for('query.view_query', query_id=query_id))

@query_bp.route('/uploads/<path:filename>')
@login_required
def download_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
