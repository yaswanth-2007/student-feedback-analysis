from datetime import datetime, timezone
from app.extensions import db


class FeedbackQuestion(db.Model):
    """Feedback question entity supporting rating scales and optional comments."""
    __tablename__ = 'feedback_questions'

    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False, default='General', index=True)
    question_type = db.Column(db.String(20), nullable=False, default='rating')  # 'rating', 'comment'
    is_required = db.Column(db.Boolean, default=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    course_questions = db.relationship('CourseQuestion', back_populates='question', cascade='all, delete-orphan', lazy='dynamic')
    responses = db.relationship('FeedbackResponse', back_populates='question', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self) -> str:
        return f"<FeedbackQuestion id={self.id} type='{self.question_type}' category='{self.category}'>"
