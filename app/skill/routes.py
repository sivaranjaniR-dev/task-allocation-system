from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, MasterSkillList
from app.decorators import admin_required

skill = Blueprint('skill', __name__)

@skill.route('/list')
@admin_required
def list():
    skills = MasterSkillList.query.order_by(MasterSkillList.created_at.desc()).all()
    total    = len(skills)
    active   = sum(1 for s in skills if s.skill_status)
    inactive = total - active
    categories = sorted(set(s.skill_category for s in skills if s.skill_category))
    return render_template('skill/list.html',
                           skills=skills,
                           total=total,
                           active=active,
                           inactive=inactive,
                           categories=categories)

@skill.route('/add', methods=['POST'])
@admin_required
def add():
    name        = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    category    = request.form.get('category', '').strip()

    if not name:
        flash('Skill name is required!', 'danger')
        return redirect(url_for('skill.list'))

    existing = MasterSkillList.query.filter_by(name=name).first()
    if existing:
        flash('Skill already exists!', 'danger')
        return redirect(url_for('skill.list'))

    new_skill = MasterSkillList(
        name           = name,
        description    = description,
        skill_category = category,
        skill_status   = True
    )
    db.session.add(new_skill)
    db.session.commit()
    flash('Skill added successfully!', 'success')
    return redirect(url_for('skill.list'))

@skill.route('/toggle/<int:skill_id>')
@admin_required
def toggle(skill_id):
    s = MasterSkillList.query.get(skill_id)
    if s:
        s.skill_status = not s.skill_status
        db.session.commit()
        flash(f'Skill {"activated" if s.skill_status else "deactivated"} successfully!', 'success')
    return redirect(url_for('skill.list'))

@skill.route('/delete/<int:skill_id>')
@admin_required
def delete(skill_id):
    s = MasterSkillList.query.get(skill_id)
    if s:
        db.session.delete(s)
        db.session.commit()
        flash('Skill deleted successfully!', 'success')
    return redirect(url_for('skill.list'))