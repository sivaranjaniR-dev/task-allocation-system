import os

class Config:
    # Secret key for session security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mysecretkey123')

    # MySQL Database connection
    SQLALCHEMY_DATABASE_URI = (
        'mysql+pymysql://root:AllIsWell@localhost/skill_allocation_db'
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False