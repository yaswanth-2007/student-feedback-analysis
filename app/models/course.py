from datetime import datetime, timezone
from app.extensions import db


class Course(db.Model):
    """Academic Course entity."""
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    course_name = db.Column(db.String(150), nullable=False, index=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id', ondelete='SET NULL'), nullable=True, index=True)
    department = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    faculty = db.relationship('Faculty', back_populates='courses')
    course_questions = db.relationship('CourseQuestion', back_populates='course', cascade='all, delete-orphan', lazy='dynamic')
    submissions = db.relationship('FeedbackSubmission', back_populates='course', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self) -> str:
        return f"<Course id={self.id} code='{self.course_code}' name='{self.course_name}'>"
