import pandas as pd
from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models import Course, FeedbackQuestion, FeedbackSubmission, FeedbackResponse
from app.services.analytics_service import AnalyticsService


def test_numeric_summary_calculation():
    """Verify mean, median, min, max, and standard deviation calculations."""
    # Ratings: 5, 4, 3, 4, 4 -> mean = 4.0, count = 5
    series = pd.Series([5, 4, 3, 4, 4])
    summary = AnalyticsService.calculate_numeric_summary(series)

    assert summary['count'] == 5
    assert summary['mean'] == 4.0
    assert summary['median'] == 4.0
    assert summary['min'] == 3
    assert summary['max'] == 5
    assert summary['std_dev'] > 0


def test_empty_dataset_and_null_ratings_handling():
    """Verify empty and NaN series return clean nulls without division by zero."""
    empty_series = pd.Series([], dtype=float)
    summary = AnalyticsService.calculate_numeric_summary(empty_series)
    assert summary['count'] == 0
    assert summary['mean'] is None
    assert summary['median'] is None

    nan_series = pd.Series([None, None, float('nan')])
    summary_nan = AnalyticsService.calculate_numeric_summary(nan_series)
    assert summary_nan['count'] == 0
    assert summary_nan['mean'] is None


def test_rating_distribution_percentages():
    """Verify discrete 1-5 rating distribution and percentage sums."""
    series = pd.Series([1, 2, 3, 4, 5, 5, 5, 4, 3, 2])  # 10 items
    dist = AnalyticsService.calculate_rating_distribution(series)

    assert dist['total_valid'] == 10
    assert dist['counts'][5] == 3
    assert dist['percentages'][5] == 30.0
    assert dist['counts'][1] == 1
    assert dist['percentages'][1] == 10.0

    # Ensure total percentages sum to ~100%
    total_pct = sum(dist['percentages'].values())
    assert 99.0 <= total_pct <= 101.0


def test_course_filtering_and_kpis(app):
    """Test database KPI retrieval with course and date filtering."""
    with app.app_context():
        course = Course.query.filter_by(course_code="TEST-101").first()
        q1 = FeedbackQuestion.query.filter_by(question_type="rating").first()

        # Insert 3 test submissions
        now = datetime.now(timezone.utc)
        for val in [5, 4, 3]:
            sub = FeedbackSubmission(course_id=course.id, submitted_at=now, survey_version=1)
            db.session.add(sub)
            db.session.flush()
            resp = FeedbackResponse(submission_id=sub.id, question_id=q1.id, rating=val, created_at=now)
            db.session.add(resp)
        db.session.commit()

        # Check KPIs
        kpis = AnalyticsService.get_dashboard_kpis(course_id=course.id)
        assert kpis['total_submissions'] == 3
        assert kpis['overall_average'] == 4.0
        assert kpis['courses_with_feedback'] == 1

        # Check course analytics
        course_stats = AnalyticsService.get_course_analytics(course_id=course.id)
        assert len(course_stats) == 1
        assert course_stats[0]['mean_rating'] == 4.0
        assert course_stats[0]['valid_responses'] == 3
        # Reliability flag: n < 5 should be False
        assert course_stats[0]['is_reliable'] is False
