from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.models import db
    db.init_app(app)

    from app.auth.routes import auth
    from app.admin.routes import admin
    from app.manager.routes import manager
    from app.employee.routes import employee
    from app.skill.routes import skill
    from app.workload.routes import workload
    from app.allocation.routes import allocation
    from app.log.routes import log
    from app.notification.routes import notification

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(manager, url_prefix='/manager')
    app.register_blueprint(employee, url_prefix='/employee')
    app.register_blueprint(skill, url_prefix='/skill')
    app.register_blueprint(workload, url_prefix='/workload')
    app.register_blueprint(allocation, url_prefix='/allocation')
    app.register_blueprint(log, url_prefix='/log')
    app.register_blueprint(notification, url_prefix='/notification')

    with app.app_context():
        db.create_all()

    @app.context_processor
    def inject_notifications():
        from flask import session
        from app.models import Notification
        if session.get('user_id'):
            unread_count = Notification.query.filter_by(
                user_id=session.get('user_id'),
                is_read=False
            ).count()
            return {'unread_count': unread_count}
        return {'unread_count': 0}

    return app