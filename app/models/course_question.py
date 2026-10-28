from app.extensions import db


class CourseQuestion(db.Model):
    """Association entity for mapping specific questions to individual courses."""
    __tablename__ = 'course_questions'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey('feedback_questions.id', ondelete='CASCADE'), nullable=False, index=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('course_id', 'question_id', name='uq_course_question'),
    )

    # Relationships
    course = db.relationship('Course', back_populates='course_questions')
    question = db.relationship('FeedbackQuestion', back_populates='course_questions')

    def __repr__(self) -> str:
        return f"<CourseQuestion course_id={self.course_id} question_id={self.question_id}>"
