from flask import session, redirect, url_for, flash
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login first!', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login first!', 'danger')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'admin':
            flash('Access denied!', 'danger')
            role = session.get('user_role')
            return redirect(url_for(f'{role}.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login first!', 'danger')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'manager':
            flash('Access denied!', 'danger')
            role = session.get('user_role')
            return redirect(url_for(f'{role}.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def employee_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login first!', 'danger')
            return redirect(url_for('auth.login'))
        if session.get('user_role') != 'employee':
            flash('Access denied!', 'danger')
            role = session.get('user_role')
            return redirect(url_for(f'{role}.dashboard'))
        return f(*args, **kwargs)
    return decorated_function