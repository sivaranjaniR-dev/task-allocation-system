from flask import Blueprint, render_template

workload = Blueprint('workload', __name__)

@workload.route('/manage')
def manage():
    return render_template('workload/manage.html')
