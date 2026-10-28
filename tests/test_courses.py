from app.extensions import db
from app.models import Course, FeedbackQuestion, FeedbackSubmission, FeedbackResponse


def test_authorized_course_creation_and_editing(auth_client, app):
    """Test administrator can create and edit courses."""
    resp = auth_client.post('/admin/courses', data={
        'course_code': 'ENG-201',
        'course_name': 'Software Architecture Patterns',
        'department': 'Software Engineering',
        'faculty_id': '',
        'description': 'Advanced system design.'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"ENG-201" in resp.data

    with app.app_context():
        course = Course.query.filter_by(course_code="ENG-201").first()
        assert course is not None
        assert course.department == "Software Engineering"

        # Edit course
        edit_resp = auth_client.post(f'/admin/courses/{course.id}/edit', data={
            'course_name': 'Updated Architecture Title',
            'department': 'Software Systems',
            'faculty_id': '',
            'description': 'Updated description.'
        }, follow_redirects=True)
        assert edit_resp.status_code == 200

        updated = db.session.get(Course, course.id)
        assert updated.course_name == 'Updated Architecture Title'
        assert updated.department == 'Software Systems'


def test_duplicate_course_code_rejection(auth_client):
    """Test that existing course codes cannot be duplicated."""
    resp = auth_client.post('/admin/courses', data={
        'course_code': 'TEST-101',  # Already exists from fixture
        'course_name': 'Duplicate Code Course',
        'department': 'Computer Science',
        'faculty_id': '',
        'description': 'Testing duplicate constraint.'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"already exists" in resp.data


def test_historical_feedback_preservation_on_deactivation(auth_client, app):
    """Verify that deactivating a course preserves its feedback submissions and history."""
    with app.app_context():
        course = Course.query.filter_by(course_code="TEST-101").first()
        q1 = FeedbackQuestion.query.first()

        # Add a submission
        sub = FeedbackSubmission(course_id=course.id, survey_version=1)
        db.session.add(sub)
        db.session.flush()
        resp_obj = FeedbackResponse(submission_id=sub.id, question_id=q1.id, rating=5)
        db.session.add(resp_obj)
        db.session.commit()

        # Deactivate course via admin action
        toggle_resp = auth_client.post(f'/admin/courses/{course.id}/toggle', follow_redirects=True)
        assert toggle_resp.status_code == 200

        deactivated = db.session.get(Course, course.id)
        assert deactivated.is_active is False

        # Feedback must remain preserved
        preserved_sub = FeedbackSubmission.query.filter_by(course_id=course.id).first()
        assert preserved_sub is not None
        assert preserved_sub.responses.count() == 1
