import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///furniture.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False