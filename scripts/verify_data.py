from app import create_app
from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportService
from app.models import Course, FeedbackSubmission, FeedbackResponse

app = create_app('development')
with app.app_context():
    courses = Course.query.all()
    submissions = FeedbackSubmission.query.count()
    responses = FeedbackResponse.query.count()
    print(f'Total Courses in DB: {len(courses)}')
    print(f'Total Submissions: {submissions}')
    print(f'Total Responses: {responses}')

    kpis = AnalyticsService.get_dashboard_kpis()
    print(f'KPIs: {kpis}')

    analytics = AnalyticsService.get_course_analytics()
    top_c = analytics[0]
    print(f'Top course: {top_c["course_code"]} ({top_c["course_name"]}) with mean {top_c["mean_rating"]}')

    csv_data = ReportService.generate_csv_summary()
    print(f'CSV Length: {len(csv_data)} bytes')

    pdf_buf = ReportService.generate_pdf_report()
    pdf_bytes = pdf_buf.getvalue()
    print(f'PDF Buffer Size: {len(pdf_bytes)} bytes, starts with: {pdf_bytes[:8]}')
    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
