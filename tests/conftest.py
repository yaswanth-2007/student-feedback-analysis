import pytest
from app import create_app
from app.extensions import db
from app.models import AdminUser, Faculty, Course, FeedbackQuestion, FeedbackSubmission, FeedbackResponse, ApplicationSetting


@pytest.fixture
def app():
    """Create and configure a clean Flask application instance for automated testing."""
    test_app = create_app('testing')

    with test_app.app_context():
        db.create_all()
        # Seed basic baseline test data
        admin = AdminUser(
            email='testadmin@university.edu',
            display_name='Test Administrator',
            is_active=True
        )
        admin.set_password('AdminPassword123!')
        db.session.add(admin)

        ApplicationSetting.set_value('survey_enabled', 'true', 'Test survey setting')

        fac = Faculty(faculty_name="Prof. Alan Turing", department="Computer Science", is_active=True)
        db.session.add(fac)
        db.session.flush()

        course = Course(
            course_code="TEST-101",
            course_name="Introduction to Unit Testing",
            department="Computer Science",
            faculty_id=fac.id,
            description="A course designed for verification tests.",
            is_active=True
        )
        db.session.add(course)

        q1 = FeedbackQuestion(
            question_text="The instructor explained materials clearly.",
            category="Instruction",
            question_type="rating",
            is_required=True,
            display_order=1,
            is_active=True
        )
        q2 = FeedbackQuestion(
            question_text="Additional thoughts or constructive feedback.",
            category="General",
            question_type="comment",
            is_required=False,
            display_order=2,
            is_active=True
        )
        db.session.add_all([q1, q2])
        db.session.commit()

        yield test_app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    """Authenticated test client logged in as testadmin@university.edu."""
    with app.app_context():
        client.post('/auth/login', data={
            'email': 'testadmin@university.edu',
            'password': 'AdminPassword123!'
        }, follow_redirects=True)
    return client
