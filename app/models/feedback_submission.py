from datetime import datetime, timezone
from app.extensions import db


class FeedbackSubmission(db.Model):
    """Anonymous feedback submission envelope.
    
    STRICT PRIVACY POLICY:
    This model explicitly does NOT contain any student identity fields,
    roll numbers, student emails, IP addresses, or browser fingerprinting.
    """
    __tablename__ = 'feedback_submissions'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    survey_version = db.Column(db.Integer, default=1, nullable=False)

    # Relationships
    course = db.relationship('Course', back_populates='submissions')
    responses = db.relationship('FeedbackResponse', back_populates='submission', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self) -> str:
        return f"<FeedbackSubmission id={self.id} course_id={self.course_id} date={self.submitted_at}>"
