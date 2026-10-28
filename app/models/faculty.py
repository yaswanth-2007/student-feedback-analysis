from datetime import datetime, timezone
from app.extensions import db


class Faculty(db.Model):
    """Faculty entity representing instructors associated with courses."""
    __tablename__ = 'faculty'

    id = db.Column(db.Integer, primary_key=True)
    faculty_name = db.Column(db.String(120), nullable=False, index=True)
    department = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    courses = db.relationship('Course', back_populates='faculty', lazy='dynamic')

    def __repr__(self) -> str:
        return f"<Faculty id={self.id} name='{self.faculty_name}'>"
