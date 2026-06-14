from flask import Blueprint, render_template, redirect, url_for, session
from app.models import db, Notification, Allocation

notification = Blueprint('notification', __name__)

@notification.route('/list')
def list():
    user_id = session.get('user_id')

    notifications = Notification.query.filter_by(
        user_id=user_id
    ).order_by(Notification.created_at.desc()).all()

    recent_allocations = Allocation.query.filter_by(
        employee_id=user_id
    ).order_by(Allocation.allocated_at.desc()).limit(10).all()

    return render_template('notification/list.html',
                           notifications=notifications,
                           recent_allocations=recent_allocations)

@notification.route('/mark_all_read')
def mark_all_read():
    user_id = session.get('user_id')
    Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).update({'is_read': True})
    db.session.commit()
    return redirect(url_for('notification.list'))