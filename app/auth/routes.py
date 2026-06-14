from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import db, User, Workload
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        user     = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id']   = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role

            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'manager':
                return redirect(url_for('manager.dashboard'))
            elif user.role == 'employee':
                return redirect(url_for('employee.dashboard'))
        else:
            flash('Invalid email or password!', 'danger')

    return render_template('auth/login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name')
        email    = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(
            name     = name,
            email    = email,
            password = generate_password_hash(password),
            role     = 'employee'
        )
        db.session.add(new_user)
        db.session.commit()
        new_workload = Workload(
            employee_id   = new_user.id,
            current_tasks = 0,
            max_threshold = 5        # ← max_tasks remove பண்ணுங்க
        )
        db.session.add(new_workload)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('auth.login'))