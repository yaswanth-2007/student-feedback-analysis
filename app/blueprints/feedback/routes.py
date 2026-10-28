from flask import render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.blueprints.feedback import feedback_bp
from app.models import Course, ApplicationSetting
from app.services.feedback_service import FeedbackService


@feedback_bp.route('/')
def portal():
    """Student feedback portal listing active courses available for evaluation."""
    survey_enabled = ApplicationSetting.get_value('survey_enabled', 'true').lower() == 'true'
    search_query = request.args.get('q', '').strip()
    dept_filter = request.args.get('department', '').strip()

    query = Course.query.filter_by(is_active=True)
    if search_query:
        query = query.filter(
            (Course.course_name.ilike(f'%{search_query}%')) |
            (Course.course_code.ilike(f'%{search_query}%'))
        )
    if dept_filter:
        query = query.filter_by(department=dept_filter)

    courses = query.order_by(Course.course_code).all()

    # Get distinct departments for filter dropdown
    all_active = Course.query.filter_by(is_active=True).all()
    departments = sorted(list(set(c.department for c in all_active if c.department)))

    return render_template(
        'public/feedback_portal.html',
        courses=courses,
        departments=departments,
        selected_dept=dept_filter,
        search_query=search_query,
        survey_enabled=survey_enabled
    )


@feedback_bp.route('/<int:course_id>', methods=['GET', 'POST'])
def feedback_form(course_id: int):
    """Anonymous feedback submission form for a specific active course."""
    survey_enabled = ApplicationSetting.get_value('survey_enabled', 'true').lower() == 'true'
    if not survey_enabled:
        flash('Evaluation survey submissions are currently closed by the academic administration.', 'warning')
        return redirect(url_for('feedback.portal'))

    course = Course.query.filter_by(id=course_id, is_active=True).first_or_404()
    questions = FeedbackService.get_course_active_questions(course.id)

    if not questions:
        flash('There are no feedback questions configured for this course yet.', 'info')
        return redirect(url_for('feedback.portal'))

    if request.method == 'POST':
        # Parse answers from form submission
        answers = {}
        for q in questions:
            raw_rating = request.form.get(f'rating_{q.id}')
            raw_comment = request.form.get(f'comment_{q.id}', '')
            answers[q.id] = {
                'rating': raw_rating if raw_rating else None,
                'comment': raw_comment
            }

        success, msg, sub_id = FeedbackService.submit_feedback(course.id, answers)
        if success:
            return redirect(url_for('feedback.success', course_id=course.id))
        else:
            flash(msg, 'danger')

    return render_template(
        'public/feedback_form.html',
        course=course,
        questions=questions
    )


@feedback_bp.route('/success')
def success():
    """Confirmation page displayed upon verified anonymous submission."""
    course_id = request.args.get('course_id', type=int)
    course = db.session.get(Course, course_id) if course_id else None
    return render_template('public/feedback_success.html', course=course)


# --- REST API Endpoints for Programmatic / Dynamic Access ---

@feedback_bp.route('/api/courses')
def api_courses():
    """JSON API returning active courses."""
    courses = Course.query.filter_by(is_active=True).order_by(Course.course_code).all()
    return jsonify([{
        'id': c.id,
        'code': c.course_code,
        'name': c.course_name,
        'department': c.department,
        'faculty': c.faculty.faculty_name if c.faculty else None
    } for c in courses])


@feedback_bp.route('/api/courses/<int:course_id>/questions')
def api_course_questions(course_id: int):
    """JSON API returning active questions for a specific course."""
    course = Course.query.filter_by(id=course_id, is_active=True).first()
    if not course:
        return jsonify({'error': 'Course not found or inactive'}), 404

    questions = FeedbackService.get_course_active_questions(course.id)
    return jsonify([{
        'id': q.id,
        'text': q.question_text,
        'category': q.category,
        'type': q.question_type,
        'is_required': q.is_required,
        'display_order': q.display_order
    } for q in questions])


@feedback_bp.route('/api/submissions', methods=['POST'])
def api_submit():
    """REST JSON endpoint for feedback submissions."""
    data = request.get_json()
    if not data or 'course_id' not in data or 'answers' not in data:
        return jsonify({'error': 'Invalid request body. Expected course_id and answers.'}), 400

    course_id = data['course_id']
    raw_answers = data['answers']
    
    # Format answers dict
    answers = {}
    for q_id_str, ans_data in raw_answers.items():
        try:
            q_id = int(q_id_str)
            answers[q_id] = {
                'rating': ans_data.get('rating'),
                'comment': ans_data.get('comment')
            }
        except ValueError:
            return jsonify({'error': f'Invalid question ID: {q_id_str}'}), 400

    success, msg, sub_id = FeedbackService.submit_feedback(course_id, answers)
    if success:
        return jsonify({'message': msg, 'submission_id': sub_id}), 201
    else:
        return jsonify({'error': msg}), 400
