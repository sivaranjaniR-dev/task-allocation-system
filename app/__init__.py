from flask import Flask
from app.models import db


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:AllIsWell@localhost/skill_allocation_db'
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # ── Register all Blueprints ──────────────────────────
    from app.auth.routes         import auth
    from app.admin.routes        import admin
    from app.manager.routes      import manager
    from app.employee.routes     import employee
    from app.log.routes          import log
    from app.notification.routes import notification
    from app.skill.routes        import skill
    from app.workload.routes     import workload

    app.register_blueprint(auth,         url_prefix='/auth')
    app.register_blueprint(admin,        url_prefix='/admin')
    app.register_blueprint(manager,      url_prefix='/manager')
    app.register_blueprint(employee,     url_prefix='/employee')
    app.register_blueprint(log,          url_prefix='/log')
    app.register_blueprint(notification, url_prefix='/notification')
    app.register_blueprint(skill,        url_prefix='/skill')
    app.register_blueprint(workload,     url_prefix='/workload')

    # ── Global context processor ─────────────────────────
    @app.context_processor
    def inject_globals():
        from flask import session
        from app.models import Notification
        unread_count = 0
        if session.get('user_id'):
            try:
                unread_count = Notification.query.filter_by(
                    user_id=session.get('user_id'),
                    is_read=False
                ).count()
            except Exception:
                unread_count = 0
        return dict(unread_count=unread_count)

    # ── Home redirect ────────────────────────────────────
    from flask import redirect, url_for, render_template

    @app.route('/')
    def home():
        return render_template('index.html')

    # ── Create DB tables ─────────────────────────────────
    with app.app_context():
        db.create_all()

    return app