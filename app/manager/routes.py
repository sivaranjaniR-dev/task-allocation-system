from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, User, Task, TaskRequiredSkill, Allocation, AllocationLog, Workload, EmployeeSkill, MasterSkillList, Notification
from app.decorators import manager_required
from datetime import datetime

manager = Blueprint('manager', __name__)


@manager.route('/dashboard')
@manager_required
def dashboard():
    total_tasks      = Task.query.count()
    pending_tasks    = Task.query.filter_by(status='pending').count()
    assigned_tasks   = Task.query.filter_by(status='assigned').count()
    completed_tasks  = Task.query.filter_by(status='completed').count()
    total_employees  = User.query.filter_by(role='employee').count()
    total_allocation = Allocation.query.count()
    recent_tasks     = Task.query.order_by(Task.created_at.desc()).limit(5).all()
    recent_allocs    = Allocation.query.order_by(Allocation.allocated_at.desc()).limit(5).all()

    return render_template('manager/dashboard.html',
                           total_tasks=total_tasks,
                           pending_tasks=pending_tasks,
                           assigned_tasks=assigned_tasks,
                           completed_tasks=completed_tasks,
                           total_employees=total_employees,
                           total_allocation=total_allocation,
                           recent_tasks=recent_tasks,
                           recent_allocs=recent_allocs)


@manager.route('/create_task', methods=['GET', 'POST'])
@manager_required
def create_task():
    skills = MasterSkillList.query.all()

    if request.method == 'POST':
        title           = request.form.get('title')
        description     = request.form.get('description')
        selected_skills = request.form.getlist('skills')
        priority        = request.form.get('priority', 'medium')
        estimated_hours = request.form.get('estimated_hours', 0.0)
        deadline        = request.form.get('deadline')

        deadline_dt      = datetime.strptime(deadline, '%Y-%m-%d').date() if deadline else None
        primary_skill_id = int(selected_skills[0]) if selected_skills else None
        primary_prof     = int(request.form.get(f'proficiency_{primary_skill_id}', 1)) if primary_skill_id else 1

        task = Task(
            title             = title,
            description       = description,
            required_skill_id = primary_skill_id,
            min_proficiency   = primary_prof,
            priority          = priority,
            estimated_hours   = float(estimated_hours),
            deadline          = deadline_dt,
            status            = 'pending',
            created_by        = session.get('user_id')
        )
        db.session.add(task)
        db.session.flush()

        for skill_id_str in selected_skills:
            sid  = int(skill_id_str)
            prof = int(request.form.get(f'proficiency_{sid}', 3))
            wt   = int(request.form.get(f'weight_{sid}', 1))
            mand = request.form.get(f'mandatory_{sid}') == '1'
            exp  = float(request.form.get(f'experience_{sid}', 0))
            db.session.add(TaskRequiredSkill(
                task_id              = task.id,
                skill_id             = sid,
                required_proficiency = prof,
                is_mandatory         = mand,
                skill_weight         = wt,
                preferred_experience = exp
            ))

        db.session.commit()
        flash('Task created successfully!', 'success')
        return redirect(url_for('manager.create_task'))

    return render_template('manager/create_task.html', skills=skills)


@manager.route('/view_tasks')
@manager_required
def view_tasks():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template('manager/view_tasks.html', tasks=tasks)


@manager.route('/trigger_allocation')
@manager_required
def trigger_allocation():
    allocations  = Allocation.query.order_by(Allocation.allocated_at.desc()).all()
    unread_count = Notification.query.filter_by(
        user_id=session.get('user_id'), is_read=False).count()
    return render_template('allocation/allocate.html',
                           allocations=allocations,
                           unread_count=unread_count)


@manager.route('/run_allocation', methods=['POST'])
@manager_required
def run_allocation():
    pending_tasks = Task.query.filter_by(status='pending').all()

    if not pending_tasks:
        flash('No pending tasks to allocate.', 'warning')
        return redirect(url_for('manager.trigger_allocation'))

    allocated_count = 0
    skipped         = []

    for task in pending_tasks:
        required_skills = TaskRequiredSkill.query.filter_by(task_id=task.id).all()

        best_employee = None
        best_score    = -1
        best_workload = None
        best_reason   = ''

        for emp in User.query.filter_by(role='employee').all():

            # Auto-create workload row if missing
            workload = Workload.query.filter_by(employee_id=emp.id).first()
            if not workload:
                workload = Workload(
                    employee_id   = emp.id,
                    current_tasks = 0,
                    max_threshold = 5
                )
                db.session.add(workload)
                db.session.flush()

            # ── Skip overloaded employees (use max_threshold) ──
            if workload.current_tasks >= workload.max_threshold:
                continue

            # ── CASE 1: Task has required skills in TaskRequiredSkill table ──
            if required_skills:
                qualified     = True
                total_score   = 0
                skill_details = []

                for req in required_skills:
                    emp_skill = EmployeeSkill.query.filter_by(
                        employee_id = emp.id,
                        skill_id    = req.skill_id
                    ).first()

                    # Mandatory skill missing → disqualify
                    if req.is_mandatory and not emp_skill:
                        qualified = False
                        break

                    if not emp_skill:
                        continue  # optional skill missing — skip but don't disqualify

                    # Proficiency check
                    if emp_skill.proficiency_level < req.required_proficiency:
                        qualified = False
                        break

                    # Experience check — don't disqualify, reduce score if experience low
                    emp_exp        = emp_skill.years_of_experience or 0.0
                    exp_penalty    = 0
                    if req.preferred_experience and req.preferred_experience > 0:
                        if emp_exp < req.preferred_experience:
                            exp_penalty = 10  # score penalty, still eligible

                    skill_score = (emp_skill.proficiency_level * (req.skill_weight or 1) * 20) - exp_penalty
                    total_score += skill_score

                    skill_name = MasterSkillList.query.get(req.skill_id)
                    sname      = skill_name.name if skill_name else f"Skill {req.skill_id}"
                    skill_details.append(
                        f"{sname}: {emp_skill.proficiency_level}/{req.required_proficiency} ✅"
                    )

                if not qualified:
                    continue

                # Workload tiebreaker
                final_score = total_score - (workload.current_tasks * 10)

                if final_score > best_score:
                    best_score    = round(total_score / len(required_skills), 1)
                    best_employee = emp
                    best_workload = workload
                    best_reason   = (
                        f"Skills matched: {', '.join(skill_details)}. "
                        f"Score: {best_score}. "
                        f"Workload: {workload.current_tasks}/{workload.max_threshold}."
                    )

            # ── CASE 2: Task has only required_skill_id ──
            elif task.required_skill_id:
                emp_skill = EmployeeSkill.query.filter_by(
                    employee_id = emp.id,
                    skill_id    = task.required_skill_id
                ).first()

                if not emp_skill:
                    continue
                if task.min_proficiency and emp_skill.proficiency_level < task.min_proficiency:
                    continue

                score = emp_skill.proficiency_level * 20 - (workload.current_tasks * 10)
                if score > best_score:
                    best_score    = emp_skill.proficiency_level * 20
                    best_employee = emp
                    best_workload = workload
                    best_reason   = (
                        f"Skill proficiency: {emp_skill.proficiency_level}/5. "
                        f"Score: {best_score}. "
                        f"Workload: {workload.current_tasks}/{workload.max_threshold}."
                    )

            # ── CASE 3: No skill requirement — pick least loaded employee ──
            else:
                score = 100 - (workload.current_tasks * 10)
                if score > best_score:
                    best_score    = 100
                    best_employee = emp
                    best_workload = workload
                    best_reason   = (
                        f"No specific skill required. "
                        f"Lowest workload: {workload.current_tasks}/{workload.max_threshold}."
                    )

        if best_employee:
            new_alloc = Allocation(
                task_id                = task.id,
                employee_id            = best_employee.id,
                reason                 = best_reason,
                allocation_reason      = best_reason,
                skill_match_score      = best_score,
                workload_at_allocation = best_workload.current_tasks,
                task_status            = 'ASSIGNED'
            )
            db.session.add(new_alloc)
            db.session.flush()

            db.session.add(AllocationLog(
                allocation_id = new_alloc.id,
                action        = 'ASSIGNED',
                message       = f"Task '{task.title}' assigned to {best_employee.name}. {best_reason}"
            ))

            db.session.add(Notification(
                user_id              = best_employee.id,
                message              = f"New task assigned: '{task.title}'",
                notification_title   = 'New Task Assigned',
                notification_message = f"Task '{task.title}' assigned. Reason: {best_reason}",
                notification_type    = 'task',
                is_read              = False
            ))

            task.status = 'assigned'
            best_workload.current_tasks += 1
            allocated_count += 1
        else:
            skipped.append(task.title)

    db.session.commit()

    if allocated_count > 0:
        flash(f'Successfully allocated {allocated_count} task(s)!', 'success')
    if skipped:
        flash(f'No suitable employee found for: {", ".join(skipped)}', 'warning')

    return redirect(url_for('manager.trigger_allocation'))


@manager.route('/allocation_log')
@manager_required
def allocation_log():
    from datetime import date
    allocations = Allocation.query.order_by(Allocation.allocated_at.desc()).all()

    total       = len(allocations)
    completed   = sum(1 for a in allocations if a.task.status == 'completed')
    in_progress = sum(1 for a in allocations if a.task.status == 'assigned')
    avg_score   = round(sum(a.skill_match_score for a in allocations) / total, 1) if total else 0

    today   = date.today()
    overdue = [a for a in allocations
               if a.task.deadline and a.task.deadline < today and a.task.status != 'completed']

    emp_stats = {}
    for a in allocations:
        eid  = a.employee_id
        name = a.employee.name
        if eid not in emp_stats:
            emp_stats[eid] = {'name': name, 'assigned': 0, 'completed': 0, 'scores': []}
        emp_stats[eid]['assigned'] += 1
        emp_stats[eid]['scores'].append(a.skill_match_score)
        if a.task.status == 'completed':
            emp_stats[eid]['completed'] += 1

    for e in emp_stats.values():
        e['avg_score'] = round(sum(e['scores']) / len(e['scores']), 1) if e['scores'] else 0

    emp_performance = sorted(emp_stats.values(), key=lambda x: x['completed'], reverse=True)

    return render_template('manager/allocation_log.html',
                           allocations=allocations,
                           total=total,
                           completed=completed,
                           in_progress=in_progress,
                           avg_score=avg_score,
                           overdue=overdue,
                           emp_performance=emp_performance,
                           today=today)


@manager.route('/employees')
@manager_required
def employees():
    emp_list = User.query.filter_by(role='employee').all()
 
    emp_data = []
    for emp in emp_list:
        skills   = EmployeeSkill.query.filter_by(employee_id=emp.id).all()
        workload = Workload.query.filter_by(employee_id=emp.id).first()
        emp_data.append({
            'emp':      emp,
            'skills':   skills,
            'workload': workload
        })
 
    return render_template('manager/employees.html',
                           employees=emp_list,
                           emp_data=emp_data)



@manager.route('/monitor_status')
@manager_required
def monitor_status():
    allocations = Allocation.query.order_by(Allocation.allocated_at.desc()).all()
    return render_template('manager/monitor_status.html', allocations=allocations)


@manager.route('/allocation_result')
@manager_required
def allocation_result():
    allocations = Allocation.query.order_by(Allocation.allocated_at.desc()).all()
    return render_template('manager/allocation_result.html', allocations=allocations)


@manager.route('/debug_allocation')
@manager_required
def debug_allocation():
    from flask import jsonify
    pending_tasks = Task.query.filter_by(status='pending').all()
    employees     = User.query.filter_by(role='employee').all()

    tasks_info = [{'id': t.id, 'title': t.title, 'status': t.status,
                   'required_skill_id': t.required_skill_id,
                   'min_proficiency': t.min_proficiency} for t in pending_tasks]

    emp_info = []
    for e in employees:
        wl     = Workload.query.filter_by(employee_id=e.id).first()
        skills = EmployeeSkill.query.filter_by(employee_id=e.id).all()
        emp_info.append({
            'id': e.id, 'name': e.name,
            'workload_current': wl.current_tasks if wl else 'NO WORKLOAD ROW',
            'workload_threshold': wl.max_threshold if wl else 'N/A',
            'skills': [{'skill_id': s.skill_id, 'proficiency': s.proficiency_level} for s in skills]
        })

    return jsonify({'pending_tasks': tasks_info, 'employees': emp_info})