import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

login_manager.login_view = 'auth.login'

def create_app(config_class=None):
	from config import Config
	if config_class is None:
		config_class = Config

	app = Flask(__name__)
	app.config.from_object(config_class)

	# Ensure upload folder exists
	os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

	db.init_app(app)
	login_manager.init_app(app)
	migrate.init_app(app, db)

	# Register blueprints (to be created later)
	from .auth_routes import auth_bp  # type: ignore
	from .query_routes import query_bp  # type: ignore
	app.register_blueprint(auth_bp)
	app.register_blueprint(query_bp)

	@app.context_processor
	def inject_user_tasks():
		from .models import Query
		from flask_login import current_user
		if current_user.is_authenticated:
			pending_count = 0
			# Simple pending logic placeholder; refined later
			try:
				if current_user.role == 'auditor':
					pending_count = Query.query.filter(Query.status.in_(['employee_submitted','manager_approved','reopened'])).count()
				elif current_user.role == 'employee':
					pending_count = Query.query.filter_by(assigned_employee_id=current_user.id, status='assigned').count()
				elif current_user.role == 'manager':
					pending_count = Query.query.filter(Query.status=='employee_submitted', Query.manager_id==current_user.id).count()
			except Exception:
				pending_count = 0
			return {'pending_tasks': pending_count}
		return {'pending_tasks': 0}

	return app

def allowed_file(filename):
	from config import Config
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

