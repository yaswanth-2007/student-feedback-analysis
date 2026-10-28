import os
from flask import Flask, render_template
from config import config_by_name, Config
from app.extensions import db, migrate, login_manager, csrf
from app.models import AdminUser


def create_app(config_name=None):
    """Application factory for Student Feedback Analysis System."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, Config))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(AdminUser, int(user_id))

    # Context processors for global template variables
    @app.context_processor
    def inject_global_template_data():
        from app.models import ApplicationSetting
        demo_mode = app.config.get('SEED_DEMO_DATA', False)
        survey_enabled = ApplicationSetting.get_value('survey_enabled', 'true').lower() == 'true'
        return {
            'is_demo_mode': demo_mode,
            'is_survey_enabled': survey_enabled,
            'app_name': 'Student Feedback Analysis System'
        }

    # Custom error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('public/error.html', error_code=404, error_title='Page Not Found', error_message='The page you requested could not be located.'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('public/error.html', error_code=403, error_title='Access Restricted', error_message='You do not have permission to access this resource.'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('public/error.html', error_code=500, error_title='System Error', error_message='An unexpected server error occurred. Please try again later.'), 500

    # Register blueprints
    from app.blueprints.public import public_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.feedback import feedback_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.analytics import analytics_bp
    from app.blueprints.reports import reports_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(feedback_bp, url_prefix='/feedback')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(analytics_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/admin/reports')

    return app
