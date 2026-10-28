from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.blueprints.admin import admin_bp
from app.extensions import db
from app.models import Course, Faculty, FeedbackQuestion, FeedbackSubmission, FeedbackResponse, ApplicationSetting
from app.services.analytics_service import AnalyticsService


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Main administrative analytics dashboard."""
    course_id = request.args.get('course_id', type=int)
    faculty_id = request.args.get('faculty_id', type=int)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            pass

    # Real database analytics
    kpis = AnalyticsService.get_dashboard_kpis(course_id, faculty_id, start_date, end_date)
    course_analytics = AnalyticsService.get_course_analytics(course_id, faculty_id, start_date, end_date)
    question_analytics = AnalyticsService.get_question_analytics(course_id, faculty_id, start_date, end_date)
    
    df = AnalyticsService.get_filtered_responses_dataframe(course_id, faculty_id, start_date=start_date, end_date=end_date)
    rating_distribution = AnalyticsService.calculate_rating_distribution(df['rating'] if not df.empty else None)
    
    insights = AnalyticsService.generate_deterministic_insights(
        course_analytics, question_analytics, rating_distribution
    )

    all_courses = Course.query.order_by(Course.course_code).all()
    all_faculty = Faculty.query.filter_by(is_active=True).order_by(Faculty.faculty_name).all()

    return render_template(
        'admin/dashboard.html',
        kpis=kpis,
        courses=course_analytics,
        questions=question_analytics,
        distribution=rating_distribution,
        insights=insights,
        all_courses=all_courses,
        all_faculty=all_faculty,
        selected_course_id=course_id,
        selected_faculty_id=faculty_id,
        start_date=start_date_str,
        end_date=end_date_str
    )


# --- COURSE MANAGEMENT ---

@admin_bp.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    """Course management: list, search, add, and inspect courses."""
    if request.method == 'POST':
        code = request.form.get('course_code', '').strip().upper()
        name = request.form.get('course_name', '').strip()
        dept = request.form.get('department', '').strip()
        fac_id = request.form.get('faculty_id', type=int)
        desc = request.form.get('description', '').strip()

        if not code or not name or not dept:
            flash('Course Code, Course Name, and Department are required.', 'danger')
            return redirect(url_for('admin.courses'))

        # Check uniqueness
        if Course.query.filter_by(course_code=code).first():
            flash(f"Course code '{code}' already exists.", 'danger')
            return redirect(url_for('admin.courses'))

        new_course = Course(
            course_code=code,
            course_name=name,
            department=dept,
            faculty_id=fac_id if fac_id else None,
            description=desc,
            is_active=True
        )
        db.session.add(new_course)
        db.session.commit()
        flash(f"Course '{code} - {name}' created successfully.", 'success')
        return redirect(url_for('admin.courses'))

    search = request.args.get('q', '').strip()
    query = Course.query
    if search:
        query = query.filter(
            (Course.course_name.ilike(f'%{search}%')) |
            (Course.course_code.ilike(f'%{search}%')) |
            (Course.department.ilike(f'%{search}%'))
        )

    all_courses = query.order_by(Course.course_code).all()
    faculty_list = Faculty.query.filter_by(is_active=True).order_by(Faculty.faculty_name).all()

    # Precalculate submission counts per course
    response_counts = {}
    for c in all_courses:
        response_counts[c.id] = FeedbackSubmission.query.filter_by(course_id=c.id).count()

    return render_template(
        'admin/courses.html',
        courses=all_courses,
        faculty_list=faculty_list,
        response_counts=response_counts,
        search_query=search
    )


@admin_bp.route('/courses/<int:course_id>/edit', methods=['POST'])
@login_required
def edit_course(course_id: int):
    """Edit course attributes."""
    course = Course.query.get_or_404(course_id)
    name = request.form.get('course_name', '').strip()
    dept = request.form.get('department', '').strip()
    fac_id = request.form.get('faculty_id', type=int)
    desc = request.form.get('description', '').strip()

    if not name or not dept:
        flash('Course Name and Department cannot be empty.', 'danger')
        return redirect(url_for('admin.courses'))

    course.course_name = name
    course.department = dept
    course.faculty_id = fac_id if fac_id else None
    course.description = desc
    db.session.commit()
    flash(f"Course '{course.course_code}' updated successfully.", 'success')
    return redirect(url_for('admin.courses'))


@admin_bp.route('/courses/<int:course_id>/toggle', methods=['POST'])
@login_required
def toggle_course(course_id: int):
    """Toggle course activation status, preserving historical feedback data."""
    course = Course.query.get_or_404(course_id)
    course.is_active = not course.is_active
    db.session.commit()
    status_str = "activated" if course.is_active else "deactivated"
    flash(f"Course '{course.course_code}' has been {status_str}.", 'info')
    return redirect(url_for('admin.courses'))


# --- QUESTION MANAGEMENT ---

@admin_bp.route('/questions', methods=['GET', 'POST'])
@login_required
def questions():
    """Feedback question management."""
    if request.method == 'POST':
        q_text = request.form.get('question_text', '').strip()
        cat = request.form.get('category', '').strip() or 'General'
        q_type = request.form.get('question_type', 'rating').strip()
        is_req = bool(request.form.get('is_required'))
        order = request.form.get('display_order', 0, type=int)

        if not q_text:
            flash('Question text cannot be empty.', 'danger')
            return redirect(url_for('admin.questions'))

        new_q = FeedbackQuestion(
            question_text=q_text,
            category=cat,
            question_type=q_type,
            is_required=is_req,
            display_order=order,
            is_active=True
        )
        db.session.add(new_q)
        db.session.commit()
        flash('Feedback question added successfully.', 'success')
        return redirect(url_for('admin.questions'))

    all_questions = FeedbackQuestion.query.order_by(FeedbackQuestion.display_order, FeedbackQuestion.id).all()
    return render_template('admin/questions.html', questions=all_questions)


@admin_bp.route('/questions/<int:question_id>/edit', methods=['POST'])
@login_required
def edit_question(question_id: int):
    """Update question configuration."""
    q = FeedbackQuestion.query.get_or_404(question_id)
    q_text = request.form.get('question_text', '').strip()
    cat = request.form.get('category', '').strip()
    is_req = bool(request.form.get('is_required'))
    order = request.form.get('display_order', 0, type=int)

    if not q_text:
        flash('Question text cannot be empty.', 'danger')
        return redirect(url_for('admin.questions'))

    q.question_text = q_text
    q.category = cat or 'General'
    q.is_required = is_req
    q.display_order = order
    db.session.commit()
    flash('Feedback question updated successfully.', 'success')
    return redirect(url_for('admin.questions'))


@admin_bp.route('/questions/<int:question_id>/toggle', methods=['POST'])
@login_required
def toggle_question(question_id: int):
    """Activate or deactivate question while protecting historical responses."""
    q = FeedbackQuestion.query.get_or_404(question_id)
    q.is_active = not q.is_active
    db.session.commit()
    status_str = "activated" if q.is_active else "deactivated"
    flash(f"Question #{q.id} has been {status_str}.", 'info')
    return redirect(url_for('admin.questions'))


# --- FEEDBACK RESPONSES & REVIEW ---

@admin_bp.route('/responses')
@login_required
def responses():
    """Protected feedback response explorer with pagination, comment redaction, and privacy guardrails."""
    page = request.args.get('page', 1, type=int)
    course_id = request.args.get('course_id', type=int)
    rating_filter = request.args.get('rating', type=int)
    search = request.args.get('q', '').strip()

    query = db.session.query(
        FeedbackResponse, FeedbackSubmission, Course, FeedbackQuestion
    ).join(
        FeedbackSubmission, FeedbackResponse.submission_id == FeedbackSubmission.id
    ).join(
        Course, FeedbackSubmission.course_id == Course.id
    ).join(
        FeedbackQuestion, FeedbackResponse.question_id == FeedbackQuestion.id
    )

    if course_id:
        query = query.filter(FeedbackSubmission.course_id == course_id)
    if rating_filter:
        query = query.filter(FeedbackResponse.rating == rating_filter)
    if search:
        query = query.filter(FeedbackResponse.comment.ilike(f'%{search}%'))

    query = query.order_by(FeedbackSubmission.submitted_at.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)

    all_courses = Course.query.order_by(Course.course_code).all()

    return render_template(
        'admin/responses.html',
        pagination=pagination,
        courses=all_courses,
        selected_course_id=course_id,
        selected_rating=rating_filter,
        search_query=search
    )


@admin_bp.route('/responses/<int:response_id>/redact', methods=['POST'])
@login_required
def redact_comment(response_id: int):
    """Redact potentially identifying text from a comment while preserving the rating."""
    resp = FeedbackResponse.query.get_or_404(response_id)
    resp.is_redacted = not resp.is_redacted
    db.session.commit()
    status_str = "redacted" if resp.is_redacted else "restored"
    flash(f"Comment #{resp.id} has been {status_str}.", 'info')
    return redirect(url_for('admin.responses'))


# --- SETTINGS AND PROFILE ---

@admin_bp.route('/settings')
@login_required
def settings():
    """Administrator profile and application-wide settings."""
    survey_enabled = ApplicationSetting.get_value('survey_enabled', 'true').lower() == 'true'
    min_reliability = ApplicationSetting.get_value('min_sample_size', '5')
    return render_template(
        'admin/settings.html',
        survey_enabled=survey_enabled,
        min_sample_size=min_reliability
    )


@admin_bp.route('/settings/password', methods=['POST'])
@login_required
def change_password():
    """Secure password change with verification of current password."""
    current_pwd = request.form.get('current_password', '')
    new_pwd = request.form.get('new_password', '')
    confirm_pwd = request.form.get('confirm_password', '')

    if not current_pwd or not new_pwd:
        flash('Please provide both current and new passwords.', 'danger')
        return redirect(url_for('admin.settings'))

    if not current_user.check_password(current_pwd):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('admin.settings'))

    if len(new_pwd) < 8:
        flash('New password must be at least 8 characters long.', 'danger')
        return redirect(url_for('admin.settings'))

    if new_pwd != confirm_pwd:
        flash('New password and confirmation do not match.', 'danger')
        return redirect(url_for('admin.settings'))

    current_user.set_password(new_pwd)
    db.session.commit()
    flash('Your password has been updated successfully.', 'success')
    return redirect(url_for('admin.settings'))


@admin_bp.route('/settings/survey', methods=['POST'])
@login_required
def update_survey_status():
    """Toggle global student feedback submission availability."""
    enabled = 'enabled' in request.form
    ApplicationSetting.set_value('survey_enabled', 'true' if enabled else 'false', 'Global survey open status')
    status_str = "opened" if enabled else "closed"
    flash(f"Student feedback portal submissions have been {status_str}.", 'info')
    return redirect(url_for('admin.settings'))
