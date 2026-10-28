import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions import db
from app.models import AdminUser


def create_admin(email: str, password: str, display_name: str):
    """Command-line utility to bootstrap an administrative user."""
    app = create_app()
    with app.app_context():
        # Ensure database tables exist
        db.create_all()

        existing = AdminUser.query.filter_by(email=email.strip().lower()).first()
        if existing:
            print(f"Error: Administrator with email '{email}' already exists.")
            sys.exit(1)

        admin = AdminUser(
            email=email.strip().lower(),
            display_name=display_name.strip(),
            is_active=True
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Success: Administrator '{display_name}' ({email}) created successfully.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Bootstrap Administrator Account")
    parser.add_argument('--email', required=True, help="Administrator email address")
    parser.add_argument('--password', required=True, help="Secure administrator password")
    parser.add_argument('--name', default="System Administrator", help="Display name")
    args = parser.parse_args()

    create_admin(args.email, args.password, args.name)
