from datetime import datetime, timezone
from app.extensions import db


class ApplicationSetting(db.Model):
    """Application-wide runtime configuration key-value storage."""
    __tablename__ = 'application_settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    @classmethod
    def get_value(cls, key: str, default: str = None) -> str:
        """Fetch setting value by key with a fallback default."""
        setting = cls.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default

    @classmethod
    def set_value(cls, key: str, value: str, description: str = None) -> None:
        """Insert or update setting value by key."""
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = str(value)
            if description:
                setting.description = description
        else:
            setting = cls(setting_key=key, setting_value=str(value), description=description)
            db.session.add(setting)
        db.session.commit()

    def __repr__(self) -> str:
        return f"<ApplicationSetting {self.setting_key}='{self.setting_value}'>"
