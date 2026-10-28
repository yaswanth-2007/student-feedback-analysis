from datetime import datetime
from flask import jsonify, request
from flask_login import login_required
from app.blueprints.analytics import analytics_bp
from app.services.analytics_service import AnalyticsService


def parse_date_params():
    """Extract start_date and end_date from request query string."""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    course_id = request.args.get('course_id', type=int)
    faculty_id = request.args.get('faculty_id', type=int)

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

    return course_id, faculty_id, start_date, end_date


@analytics_bp.route('/admin/dashboard-stats')
@login_required
def api_dashboard_stats():
    """Real database KPIs for AJAX dashboard filtering."""
    course_id, faculty_id, start_date, end_date = parse_date_params()
    kpis = AnalyticsService.get_dashboard_kpis(course_id, faculty_id, start_date, end_date)
    return jsonify(kpis)


@analytics_bp.route('/admin/analytics/courses')
@login_required
def api_course_analytics():
    """Aggregated course statistics with distribution and reliability flags."""
    course_id, faculty_id, start_date, end_date = parse_date_params()
    courses = AnalyticsService.get_course_analytics(course_id, faculty_id, start_date, end_date)
    return jsonify(courses)


@analytics_bp.route('/admin/analytics/questions')
@login_required
def api_question_analytics():
    """Aggregated question averages and rating distribution."""
    course_id, faculty_id, start_date, end_date = parse_date_params()
    questions = AnalyticsService.get_question_analytics(course_id, faculty_id, start_date, end_date)
    return jsonify(questions)


@analytics_bp.route('/admin/analytics/distribution')
@login_required
def api_rating_distribution():
    """Discrete 1-5 rating distribution with percentages."""
    course_id, faculty_id, start_date, end_date = parse_date_params()
    df = AnalyticsService.get_filtered_responses_dataframe(course_id, faculty_id, start_date=start_date, end_date=end_date)
    distribution = AnalyticsService.calculate_rating_distribution(df['rating'] if not df.empty else None)
    return jsonify(distribution)


@analytics_bp.route('/admin/analytics/trends')
@login_required
def api_trends():
    """Chronological submission and average rating trends."""
    course_id, faculty_id, start_date, end_date = parse_date_params()
    interval = request.args.get('interval', 'day')
    trends = AnalyticsService.get_submission_trends(course_id, faculty_id, start_date, end_date, interval)
    return jsonify(trends)
