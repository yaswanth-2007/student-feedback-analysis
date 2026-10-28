from app.extensions import db
from app.models import Course, FeedbackQuestion, FeedbackSubmission, FeedbackResponse
from app.services.feedback_service import FeedbackService


def test_valid_anonymous_submission(client, app):
    """Test valid anonymous student feedback submission."""
    with app.app_context():
        course = Course.query.filter_by(course_code="TEST-101").first()
        q1 = FeedbackQuestion.query.filter_by(question_type="rating").first()
        q2 = FeedbackQuestion.query.filter_by(question_type="comment").first()

        resp = client.post(f'/feedback/{course.id}', data={
            f'rating_{q1.id}': '5',
            f'comment_{q2.id}': 'Outstanding instruction and clear explanations.'
        }, follow_redirects=True)

        assert resp.status_code == 200
        assert b"Thank You for Your Feedback!" in resp.data

        # Verify database record
        sub = FeedbackSubmission.query.filter_by(course_id=course.id).first()
        assert sub is not None
        assert not hasattr(sub, 'student_id')
        assert not hasattr(sub, 'ip_address')

        responses = FeedbackResponse.query.filter_by(submission_id=sub.id).all()
        assert len(responses) == 2
        r_rating = [r for r in responses if r.question_id == q1.id][0]
        assert r_rating.rating == 5


def test_invalid_rating_below_one(app):
    """Test rejection when rating is below 1."""
    with app.app_context():
        course = Course.query.filter_by(course_code="TEST-101").first()
        q1 = FeedbackQuestion.query.filter_by(question_type="rating").first()

        success, msg, sub_id = FeedbackService.submit_feedback(
            course.id,
            {q1.id: {'rating': 0, 'comment': None}}
        )
        assert not success
        assert "must be an integer between 1 and 5" in msg
        assert sub_id is None


def test_invalid_rating_above_five(app):
    """Test rejection when rating is above 5."""
    with app.app_context():
        course = Course.query.filter_by(course_code="TEST-101").first()
        q1 = FeedbackQuestion.query.filter_by(question_type="rating").first()

        success, msg, sub_id = FeedbackService.submit_feedback(
            course.id,
            {q1.id: {'rating': 6, 'comment': None}}
        )
        assert not success
        assert "must be an integer between 1 and 5" in msg
        assert sub_id is None


def test_missing_required_response_rejection(app):
    """Test rejection when mandatory question is unanswered."""
    with app.app_context():
        course = Course.query.filter_by(course_code="TEST-101").first()
        q1 = FeedbackQuestion.query.filter_by(question_type="rating", is_required=True).first()

        success, msg, sub_id = FeedbackService.submit_feedback(
            course.id,
            {q1.id: {'rating': None, 'comment': None}}
        )
        assert not success
        assert "Please provide a rating for the required question" in msg


def test_inactive_course_rejection(app):
    """Test that inactive courses cannot accept evaluations."""
    with app.app_context():
        course = Course.query.filter_by(course_code="TEST-101").first()
        course.is_active = False
        db.session.commit()

        q1 = FeedbackQuestion.query.filter_by(question_type="rating").first()
        success, msg, sub_id = FeedbackService.submit_feedback(
            course.id,
            {q1.id: {'rating': 4, 'comment': None}}
        )
        assert not success
        assert "inactive" in msg.lower()


def test_transaction_rollback_integrity(app):
    """Verify database transaction rolls back completely on any unexpected error."""
    with app.app_context():
        course = Course.query.filter_by(course_code="TEST-101").first()
        initial_sub_count = FeedbackSubmission.query.count()
        initial_resp_count = FeedbackResponse.query.count()

        # Submit invalid rating type to trigger failure after validation
        success, msg, sub_id = FeedbackService.submit_feedback(
            course.id,
            {999999: {'rating': 'invalid_string', 'comment': None}}
        )
        assert not success

        # Counts must remain unchanged
        assert FeedbackSubmission.query.count() == initial_sub_count
        assert FeedbackResponse.query.count() == initial_resp_count
