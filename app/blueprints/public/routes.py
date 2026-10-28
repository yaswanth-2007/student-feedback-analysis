from flask import render_template
from app.blueprints.public import public_bp
from app.models import Course, ApplicationSetting


@public_bp.route('/')
def landing():
    """Public landing page introducing the institutional feedback system."""
    active_courses = Course.query.filter_by(is_active=True).order_by(Course.course_code).all()
    survey_enabled = ApplicationSetting.get_value('survey_enabled', 'true').lower() == 'true'
    return render_template(
        'public/landing.html',
        courses=active_courses,
        survey_enabled=survey_enabled
    )
