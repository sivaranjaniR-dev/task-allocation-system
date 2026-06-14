from flask import Blueprint, render_template, redirect, url_for, flash
from app.models import db, Allocation, Task, User, EmployeeSkill, Workload
from app.decorators import manager_required

allocation = Blueprint('allocation', __name__)


@allocation.route('/trigger_allocation')
@manager_required
def trigger_allocation():
    allocations = Allocation.query.all()
    return render_template('manager/trigger_allocation.html',
                           allocations=allocations)


@allocation.route('/run_allocation', methods=['POST'])
@manager_required
def run_allocation():
    pending_tasks = Task.query.filter_by(status='pending').all()
    for task in pending_tasks:
        best_employee = None
        best_score = 0
        employees = User.query.filter_by(role='employee').all()
        for emp in employees:
            workload = Workload.query.filter_by(employee_id=emp.id).first()
            if workload and workload.current_tasks >= workload.max_tasks:
                continue
            skill_match = EmployeeSkill.query.filter_by(
                employee_id=emp.id,
                skill_id=task.required_skill_id
            ).first()
            if skill_match:
                score = skill_match.proficiency_level * 20
                if score > best_score:
                    best_score = score
                    best_employee = emp
        if best_employee:
            workload = Workload.query.filter_by(
                employee_id=best_employee.id).first()
            alloc = Allocation(
                task_id=task.id,
                employee_id=best_employee.id,
                allocation_reason=f"Skill match {best_score}% with available workload",
                skill_match_score=best_score,
                workload_at_allocation=workload.current_tasks if workload else 0,
                task_status='ASSIGNED'
            )
            task.status = 'assigned'
            db.session.add(alloc)
    db.session.commit()
    flash('Allocation completed!', 'success')
    return redirect(url_for('allocation.trigger_allocation'))