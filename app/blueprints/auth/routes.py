from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.models import AdminUser


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Administrator login endpoint with CSRF verification and generic error responses."""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Please enter both your email address and password.', 'danger')
            return render_template('auth/login.html', email=email)

        user = AdminUser.query.filter_by(email=email).first()

        # Generic authentication failure message to prevent user enumeration
        if not user or not user.check_password(password):
            flash('Invalid email address or password. Please try again.', 'danger')
            return render_template('auth/login.html', email=email)

        if not user.is_active:
            flash('This administrator account has been disabled. Please contact system support.', 'danger')
            return render_template('auth/login.html', email=email)

        login_user(user, remember=remember)
        flash(f"Welcome back, {user.display_name}!", 'success')

        next_page = request.args.get('next')
        # Validate that redirect target is safe and internal
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('admin.dashboard')
        return redirect(next_page)

    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    """Administrator logout clearing active session."""
    logout_user()
    flash('You have been signed out successfully.', 'info')
    return redirect(url_for('auth.login'))
