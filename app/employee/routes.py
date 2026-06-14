from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, User, Task, MasterSkillList, EmployeeSkill, Allocation, Workload, Notification
from app.decorators import employee_required
from werkzeug.security import generate_password_hash

employee = Blueprint('employee', __name__)


@employee.route('/dashboard')
@employee_required
def dashboard():
    user_id = session.get('user_id')
    assigned_tasks = Allocation.query.filter_by(employee_id=user_id).count()
    completed_tasks = db.session.query(Allocation).join(Task).filter(
        Allocation.employee_id == user_id,
        Task.status == 'completed'
    ).count()
    total_skills = EmployeeSkill.query.filter_by(employee_id=user_id).count()
    recent_allocations = Allocation.query.filter_by(employee_id=user_id).order_by(Allocation.allocated_at.desc()).limit(5).all()
    my_skills = EmployeeSkill.query.filter_by(employee_id=user_id).all()
    recent_notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(3).all()

    workload_info = Workload.query.filter_by(employee_id=user_id).first()
    if not workload_info:
        workload_info = Workload(
            employee_id   = user_id,
            current_tasks = 0,
            max_tasks     = 10,
            max_threshold = 5
        )
        db.session.add(workload_info)
        db.session.commit()

    return render_template('employee/dashboard.html',
                           assigned_tasks=assigned_tasks,
                           completed_tasks=completed_tasks,
                           total_skills=total_skills,
                           recent_allocations=recent_allocations,
                           my_skills=my_skills,
                           recent_notifications=recent_notifications,
                           unread_count=Notification.query.filter_by(user_id=user_id, is_read=False).count(),
                           workload_info=workload_info)


@employee.route('/profile', methods=['GET', 'POST'])
@employee_required
def profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if request.method == 'POST':
        user.name = request.form.get('name')
        user.phone_number = request.form.get('phone_number')
        user.aadhar_no = request.form.get('aadhar_no')
        user.gender = request.form.get('gender')

        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password:
            if new_password == confirm_password:
                user.password = generate_password_hash(new_password)
                flash('Password updated successfully!', 'success')
            else:
                flash('Passwords do not match!', 'danger')
                return redirect(url_for('employee.profile'))

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('employee.profile'))

    return render_template('employee/profile.html', user=user)


@employee.route('/skill_profile', methods=['GET', 'POST'])
@employee_required
def skill_profile():
    user_id = session.get('user_id')
    all_skills = MasterSkillList.query.all()
    my_skills = EmployeeSkill.query.filter_by(employee_id=user_id).all()

    if request.method == 'POST':
        skill_id = request.form.get('skill_id')
        proficiency_level = request.form.get('proficiency_level')
        years_experience = request.form.get('years_experience')
        certified = request.form.get('certified')
        remarks = request.form.get('remarks')

        existing = EmployeeSkill.query.filter_by(
            employee_id=user_id,
            skill_id=skill_id
        ).first()

        if existing:
            existing.proficiency_level = int(proficiency_level)
            existing.years_of_experience = float(years_experience) if years_experience else 0.0
            existing.certified = True if certified else False
            existing.remarks = remarks
            db.session.commit()
            flash('Skill updated successfully!', 'success')
        else:
            new_skill = EmployeeSkill(
                employee_id=user_id,
                skill_id=int(skill_id),
                proficiency_level=int(proficiency_level),
                years_of_experience=float(years_experience) if years_experience else 0.0,
                certified=True if certified else False,
                remarks=remarks
            )
            db.session.add(new_skill)
            db.session.commit()
            flash('Skill added successfully!', 'success')

        return redirect(url_for('employee.skill_profile'))

    return render_template('employee/skill_profile.html',
                           all_skills=all_skills,
                           my_skills=my_skills)

@employee.route('/delete_skill/<int:skill_id>')
@employee_required
def delete_skill(skill_id):
    skill = EmployeeSkill.query.get(skill_id)
    db.session.delete(skill)
    db.session.commit()
    flash('Skill deleted successfully!', 'success')
    return redirect(url_for('employee.skill_profile'))


@employee.route('/view_tasks')
@employee_required
def view_tasks():
    user_id = session.get('user_id')
    allocations = Allocation.query.filter_by(employee_id=user_id).all()
    return render_template('employee/view_tasks.html', allocations=allocations)

@employee.route('/allocation_explanation')
@employee_required
def allocation_explanation():
    user_id = session.get('user_id')
    allocations = Allocation.query.filter_by(
        employee_id=user_id
    ).order_by(Allocation.allocated_at.desc()).all()
    return render_template('employee/allocation_explanation.html',
                           allocations=allocations)

@employee.route('/update_task_status', methods=['GET', 'POST'])
@employee_required
def update_task_status():
    user_id = session.get('user_id')
    allocations = Allocation.query.filter_by(
        employee_id=user_id
    ).order_by(Allocation.allocated_at.desc()).all()

    if request.method == 'POST':
        allocation_id = request.form.get('allocation_id')
        status        = request.form.get('status')
        alloc = Allocation.query.get(allocation_id)
        if alloc and alloc.employee_id == user_id:
            alloc.task_status = status
            db.session.commit()
            flash('Task status updated successfully!', 'success')
        return redirect(url_for('employee.update_task_status'))

    return render_template('employee/update_task_status.html',
                           allocations=allocations)
                           