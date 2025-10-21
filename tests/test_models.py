import unittest
from app import create_app, db
from app.models import User, Query, Category, SubCategory, QueryStatus
from werkzeug.security import generate_password_hash

class ModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=__import__('config').TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.auditor = User(username='aud', password_hash=generate_password_hash('pw'), role='auditor')
        self.employee = User(username='emp', password_hash=generate_password_hash('pw'), role='employee')
        self.manager = User(username='mgr', password_hash=generate_password_hash('pw'), role='manager')
        db.session.add_all([self.auditor, self.employee, self.manager])
        db.session.flush()
        self.cat = Category(name='TestCat')
        db.session.add(self.cat)
        db.session.flush()
        self.sub = SubCategory(name='TestSub', category_id=self.cat.id)
        db.session.add(self.sub)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_query_status_flow(self):
        q = Query(category_id=self.cat.id, subcategory_id=self.sub.id, auditor_id=self.auditor.id,
                  assigned_employee_id=self.employee.id, status=QueryStatus.ASSIGNED.value)
        db.session.add(q)
        db.session.commit()
        self.assertEqual(q.status, QueryStatus.ASSIGNED.value)
        q.status = QueryStatus.EMPLOYEE_SUBMITTED.value
        db.session.commit()
        self.assertEqual(q.status, QueryStatus.EMPLOYEE_SUBMITTED.value)
        q.status = QueryStatus.MANAGER_APPROVED.value
        db.session.commit()
        self.assertEqual(q.status, QueryStatus.MANAGER_APPROVED.value)
        q.status = QueryStatus.CLOSED.value
        db.session.commit()
        self.assertEqual(q.status, QueryStatus.CLOSED.value)

if __name__ == '__main__':
    unittest.main()
