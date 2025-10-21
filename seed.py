from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, Category, SubCategory, QueryTemplate

app = create_app()

with app.app_context():
    db.create_all()
    # Ensure baseline sample users exist (idempotent)
    sample_users = [
        ('auditor1','Auditor One','auditor'),
        ('auditor2','Auditor Two','auditor'),
        ('auditor3','Auditor Three','auditor'),
        ('employee1','Employee One','employee'),
        ('employee2','Employee Two','employee'),
        ('employee3','Employee Three','employee'),
        ('employee4','Employee Four','employee'),
        ('employee5','Employee Five','employee'),
        ('manager1','Manager One','manager'),
        ('manager2','Manager Two','manager')
    ]
    existing = {u.username for u in User.query.filter(User.username.in_([x[0] for x in sample_users])).all()}
    new_users = []
    for uname, fullname, role in sample_users:
        if uname not in existing:
            new_users.append(User(username=uname, password_hash=generate_password_hash('password'), role=role, full_name=fullname))
    if new_users:
        db.session.add_all(new_users)
        print(f"Added {len(new_users)} new users.")
    else:
        print("All sample users already present.")
    if not Category.query.first():
        cat1 = Category(name='Financial')
        cat2 = Category(name='Operational')
        db.session.add_all([cat1, cat2])
        db.session.flush()
        sub1 = SubCategory(name='Accounts Payable', category_id=cat1.id)
        sub2 = SubCategory(name='Accounts Receivable', category_id=cat1.id)
        sub3 = SubCategory(name='Branch Operations', category_id=cat2.id)
        db.session.add_all([sub1, sub2, sub3])
        db.session.flush()
        t1 = QueryTemplate(category_id=cat1.id, subcategory_id=sub1.id, text='Provide details of outstanding vendor invoices over 90 days.')
        t2 = QueryTemplate(category_id=cat1.id, subcategory_id=sub2.id, text='List top 10 overdue customer receivables.')
        t3 = QueryTemplate(category_id=cat2.id, subcategory_id=sub3.id, text='Describe daily cash reconciliation process.')
        db.session.add_all([t1, t2, t3])
    db.session.commit()
    print('Seed data inserted.')
