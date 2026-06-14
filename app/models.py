from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 1. Company Table
class Company(db.Model):
    __tablename__ = 'company'
    company_id          = db.Column('company_id', db.Integer, primary_key=True)
    company_name        = db.Column('company_name', db.String(30), nullable=False)
    company_address     = db.Column('company_address', db.String(100))
    company_email       = db.Column('company_email', db.String(30))
    company_phone       = db.Column('company_phone', db.String(12))
    company_website     = db.Column('company_website', db.String(50))
    company_description = db.Column('company_description', db.String(100))
    established_year    = db.Column('established_year', db.Integer)
    created_at          = db.Column('created_at', db.DateTime, default=datetime.utcnow)

# 2. Users Table
class User(db.Model):
    __tablename__ = 'users'
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(30), nullable=False)
    email        = db.Column(db.String(50), unique=True, nullable=False)
    password     = db.Column(db.String(200), nullable=False)
    role         = db.Column(db.Enum('admin', 'manager', 'employee'), default='employee')
    phone_number = db.Column(db.String(14))
    aadhar_no    = db.Column(db.String(14), unique=True)
    gender       = db.Column(db.Enum('male', 'female'))
    company_id   = db.Column(db.Integer, db.ForeignKey('company.company_id'), nullable=True)
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

# 3. Master Skill List Table
class MasterSkillList(db.Model):
    __tablename__ = 'master_skill_list'
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(30), unique=True, nullable=False)
    description    = db.Column(db.String(50))
    skill_category = db.Column(db.String(50), nullable=True)
    skill_status   = db.Column(db.Boolean, default=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
# 4. Employee Skills Table
class EmployeeSkill(db.Model):
    __tablename__ = 'employee_skills'
    id                  = db.Column(db.Integer, primary_key=True)
    employee_id         = db.Column(db.Integer, db.ForeignKey('users.id'))
    skill_id            = db.Column(db.Integer, db.ForeignKey('master_skill_list.id'))
    proficiency_level   = db.Column(db.Integer, nullable=False)
    years_of_experience = db.Column(db.Float, default=0.0)
    certified           = db.Column(db.Boolean, default=False)
    certification_name  = db.Column(db.String(100), default='')
    remarks             = db.Column(db.Text, default='')
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    skill = db.relationship('MasterSkillList', backref='employee_skills')

# 5. Tasks Table
class Task(db.Model):
    __tablename__ = 'tasks'
    id                = db.Column(db.Integer, primary_key=True)
    title             = db.Column(db.String(100), nullable=False)
    description       = db.Column(db.Text)
    priority          = db.Column(db.Enum('low', 'medium', 'high'), default='medium')
    status            = db.Column(db.Enum('pending', 'assigned', 'completed'), default='pending')
    estimated_hours   = db.Column(db.Float, default=0.0)
    deadline          = db.Column(db.Date)
    required_skill_id = db.Column(db.Integer, db.ForeignKey('master_skill_list.id'), nullable=True)
    min_proficiency   = db.Column(db.Integer, default=1)
    created_by        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

# 6. Task Required Skills Table
class TaskRequiredSkill(db.Model):
    __tablename__ = 'task_required_skills'
    id                   = db.Column(db.Integer, primary_key=True)
    task_id              = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    skill_id             = db.Column(db.Integer, db.ForeignKey('master_skill_list.id'))
    required_proficiency = db.Column(db.Integer, nullable=False)
    is_mandatory         = db.Column(db.Boolean, default=True)
    skill_weight         = db.Column(db.Integer, default=1)
    preferred_experience = db.Column(db.Float)

# 7. Workload Table
# Replace the Workload class in models.py with this:

class Workload(db.Model):
    __tablename__ = 'workload'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    current_tasks = db.Column(db.Integer, default=0)
    max_threshold = db.Column(db.Integer, default=5)
    availability_status = db.Column(db.String(20), default='available')
    employee = db.relationship('User', backref='workload')

# 8. Allocation Table
class Allocation(db.Model):
    __tablename__ = 'allocation'
    id                     = db.Column(db.Integer, primary_key=True)
    task_id                = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    employee_id            = db.Column(db.Integer, db.ForeignKey('users.id'))
    reason                 = db.Column(db.Text)
    allocation_reason      = db.Column(db.Text)
    skill_match_score      = db.Column(db.Float, default=0.0)
    workload_at_allocation = db.Column(db.Integer, default=0)
    task_status            = db.Column(db.String(20), default='ASSIGNED')
    allocated_at           = db.Column(db.DateTime, default=datetime.utcnow)
    task     = db.relationship('Task', backref='allocation')
    employee = db.relationship('User', backref='allocations')

# 9. Allocation Log Table
class AllocationLog(db.Model):
    __tablename__ = 'allocation_log'
    id            = db.Column(db.Integer, primary_key=True)
    allocation_id = db.Column(db.Integer, db.ForeignKey('allocation.id'))
    action        = db.Column(db.String(50))
    message       = db.Column(db.Text)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

# 10. Notifications Table
class Notification(db.Model):
    __tablename__ = 'notifications'
    id                   = db.Column(db.Integer, primary_key=True)
    user_id              = db.Column(db.Integer, db.ForeignKey('users.id'))
    message              = db.Column(db.Text)
    is_read              = db.Column(db.Boolean, default=False)
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)
    notification_title   = db.Column(db.String(100))
    notification_type    = db.Column(db.String(20), default='task')
    notification_message = db.Column(db.Text)