from datetime import datetime, timezone
from flask import render_template, request, Response, send_file
from flask_login import login_required
from app.blueprints.reports import reports_bp
from app.models import Course, Faculty
from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportService


def parse_filter_args():
    """Extract standard filtering arguments."""
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

    return course_id, faculty_id, start_date, end_date, start_date_str, end_date_str


@reports_bp.route('/')
@login_required
def index():
    """Reports configuration and interactive preview dashboard."""
    course_id, faculty_id, start_date, end_date, s_str, e_str = parse_filter_args()

    kpis = AnalyticsService.get_dashboard_kpis(course_id, faculty_id, start_date, end_date)
    courses = AnalyticsService.get_course_analytics(course_id, faculty_id, start_date, end_date)
    questions = AnalyticsService.get_question_analytics(course_id, faculty_id, start_date, end_date)

    all_courses = Course.query.order_by(Course.course_code).all()
    all_faculty = Faculty.query.filter_by(is_active=True).order_by(Faculty.faculty_name).all()

    return render_template(
        'admin/reports.html',
        kpis=kpis,
        courses=courses,
        questions=questions,
        all_courses=all_courses,
        all_faculty=all_faculty,
        selected_course_id=course_id,
        selected_faculty_id=faculty_id,
        start_date=s_str,
        end_date=e_str
    )


@reports_bp.route('/summary.csv')
@login_required
def export_csv():
    """Download RFC-4180 compliant CSV analytical summary."""
    course_id, faculty_id, start_date, end_date, _, _ = parse_filter_args()
    csv_data = ReportService.generate_csv_summary(course_id, faculty_id, start_date, end_date)

    filename = f"feedback_analysis_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@reports_bp.route('/summary.pdf')
@login_required
def export_pdf():
    """Download publication-quality PDF report with ReportLab tables and embedded charts."""
    course_id, faculty_id, start_date, end_date, _, _ = parse_filter_args()
    pdf_buffer = ReportService.generate_pdf_report(course_id, faculty_id, start_date, end_date)

    filename = f"feedback_analysis_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )
