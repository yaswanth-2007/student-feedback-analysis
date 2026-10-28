from datetime import datetime, timezone
from app.extensions import db


class FeedbackResponse(db.Model):
    """Individual question answer belonging to a feedback submission."""
    __tablename__ = 'feedback_responses'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('feedback_submissions.id', ondelete='CASCADE'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('feedback_questions.id', ondelete='CASCADE'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=True)  # Valid range: 1 through 5
    comment = db.Column(db.Text, nullable=True)
    is_redacted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('submission_id', 'question_id', name='uq_submission_question'),
        db.CheckConstraint('rating IS NULL OR (rating >= 1 AND rating <= 5)', name='ck_rating_range'),
    )

    # Relationships
    submission = db.relationship('FeedbackSubmission', back_populates='responses')
    question = db.relationship('FeedbackQuestion', back_populates='responses')

    def __repr__(self) -> str:
        return f"<FeedbackResponse id={self.id} q_id={self.question_id} rating={self.rating}>"
