from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, User, Task, MasterSkillList, Company, Workload, Allocation, AllocationLog
from app.decorators import admin_required

admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
@admin_required
def dashboard():
    total_users = User.query.count()
    total_tasks = Task.query.count()
    total_skills = MasterSkillList.query.count()
    total_allocations = Allocation.query.count()
    pending_tasks = Task.query.filter_by(status='pending').count()
    assigned_tasks = Task.query.filter_by(status='assigned').count()
    completed_tasks = Task.query.filter_by(status='completed').count()
    recent_allocations = Allocation.query.order_by(Allocation.allocated_at.desc()).limit(5).all()
    recent_logs = AllocationLog.query.order_by(AllocationLog.created_at.desc()).limit(5).all()

    # System alerts
    system_alerts = []

    if pending_tasks > 0:
        system_alerts.append({
            'icon': 'fas fa-tasks',
            'color': '#fd7e14',
            'message': f'{pending_tasks} task(s) pending allocation!',
            'type': 'warning'
        })

    new_users = User.query.order_by(User.created_at.desc()).limit(3).all()
    for user in new_users:
        system_alerts.append({
            'icon': 'fas fa-user-plus',
            'color': '#3b5bdb',
            'message': f'New user {user.name} registered!',
            'type': 'info'
        })

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_tasks=total_tasks,
                           total_skills=total_skills,
                           total_allocations=total_allocations,
                           pending_tasks=pending_tasks,
                           assigned_tasks=assigned_tasks,
                           completed_tasks=completed_tasks,
                           recent_allocations=recent_allocations,
                           recent_logs=recent_logs,
                           system_alerts=system_alerts)
@admin.route('/users')
def users():
    from app.models import User
    users = User.query.order_by(User.created_at.desc()).all()
    unread_count = 0
    return render_template('admin/users.html', users=users, unread_count=unread_count)

@admin.route('/change_role/<int:user_id>', methods=['POST'])
@admin_required
def change_role(user_id):
    user = User.query.get(user_id)
    user.role = request.form.get('role')
    db.session.commit()
    flash('Role updated successfully!', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/delete_user/<int:user_id>')
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/company', methods=['GET', 'POST'])
@admin_required
def company():
    company = Company.query.first()
    
    # Company இல்லன்னா create பண்ணு
    if not company:
        company = Company(
            name='TechNova Solutions',
            address='Chennai, Tamil Nadu',
            email='technova@gmail.com',
            phone='9876543210',
            website='www.technovasolutions.com'
        )
        db.session.add(company)
        db.session.commit()

    if request.method == 'POST':
        company.name = request.form.get('name')
        company.address = request.form.get('address')
        company.email = request.form.get('email')
        company.phone = request.form.get('phone')
        company.website = request.form.get('website')
        db.session.commit()
        flash('Company details updated!', 'success')
        return redirect(url_for('admin.company'))

    return render_template('admin/company.html', company=company)
@admin.route('/workload')
@admin_required
def workload():
    workloads = Workload.query.all()
    return render_template('admin/workload.html', workloads=workloads)

@admin.route('/set_workload/<int:workload_id>', methods=['POST'])
@admin_required
def set_workload(workload_id):
    w = Workload.query.get(workload_id)
    w.max_threshold       = int(request.form.get('max_threshold', 5))
    w.availability_status = request.form.get('availability_status', 'available')
    db.session.commit()
    flash('Workload updated successfully!', 'success')
    return redirect(url_for('admin.workload'))