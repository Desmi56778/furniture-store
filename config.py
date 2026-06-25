import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'запасной-ключ')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://...')
    SQLALCHEMY_TRACK_MODIFICATIONS = False