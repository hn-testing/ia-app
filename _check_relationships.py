from app import create_app, db
from app.models import Query

app = create_app()
with app.app_context():
    q = Query.query.first()
    if q:
        print('Query first:', q.id, 'Category obj:', bool(q.category), 'Category name:', getattr(q.category,'name',None))
    else:
        print('No Query rows yet.')
