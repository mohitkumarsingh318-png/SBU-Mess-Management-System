from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()


def _bootstrap_admin_from_environment(app):
    """Create the initial admin when explicitly configured through env vars."""
    from app.models import User

    setting_names = (
        'ADMIN_USERNAME',
        'ADMIN_EMAIL',
        'ADMIN_FULL_NAME',
        'ADMIN_PASSWORD',
    )
    settings = {
        name: os.environ.get(name, '').strip()
        for name in setting_names
    }
    settings['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', '')
    if not any(settings.values()):
        return

    missing_settings = [
        name for name, value in settings.items()
        if not value.strip()
    ]
    if missing_settings:
        raise RuntimeError(
            'Admin bootstrap requires all four settings: '
            + ', '.join(setting_names)
        )
    if not os.environ.get('DATABASE_URL'):
        raise RuntimeError('Set DATABASE_URL before bootstrapping an admin account.')
    if len(settings['ADMIN_PASSWORD']) < 12:
        raise RuntimeError('ADMIN_PASSWORD must be at least 12 characters.')

    existing_user = User.query.filter_by(
        username=settings['ADMIN_USERNAME']
    ).first()
    if existing_user:
        if (
            existing_user.email == settings['ADMIN_EMAIL']
            and existing_user.role == 'admin'
            and existing_user.is_active
        ):
            app.logger.info('Admin bootstrap account already exists.')
            return
        raise RuntimeError('ADMIN_USERNAME is already used by another account.')

    existing_email = User.query.filter_by(email=settings['ADMIN_EMAIL']).first()
    if existing_email:
        raise RuntimeError('ADMIN_EMAIL is already used by another account.')

    user = User(
        username=settings['ADMIN_USERNAME'],
        email=settings['ADMIN_EMAIL'],
        full_name=settings['ADMIN_FULL_NAME'],
        role='admin',
    )
    user.set_password(settings['ADMIN_PASSWORD'])
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        existing_user = User.query.filter_by(
            username=settings['ADMIN_USERNAME']
        ).first()
        if (
            existing_user
            and existing_user.email == settings['ADMIN_EMAIL']
            and existing_user.role == 'admin'
            and existing_user.is_active
        ):
            app.logger.info('Admin bootstrap account already exists.')
            return
        raise RuntimeError(
            'Could not create the admin account; the username or email may be in use.'
        ) from error
    app.logger.info('Admin bootstrap account created.')


def create_app():
    load_dotenv()
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif database_url and database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///mess_management.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    
    # Email Configuration (configure with your SMTP settings)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT') or 587)
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@example.com'
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.staff import staff_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Create tables
    with app.app_context():
        db.create_all()
        _bootstrap_admin_from_environment(app)
    
    return app
