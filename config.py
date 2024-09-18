import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')
    DATABASE_URI = os.environ.get('DATABASE_URI', 'postgresql://postgres:postgres@db:5432/lac_fullstack_dev')
