import os


"""
NOTE:
In a typical production environment, sensitive information such as `SECRET_KEY` and `DATABASE_URL` 
wouldn't have some default values like 'your_secret_key', but for this quick example project, 
I just used `SECRET_KEY` for ease of setup  and testing purposes. In a real-world scenario or with more time, I would
remove any default value and use secure, randomly generated key, and securely share sensitive credentials across environments.
"""

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')
    DATABASE_URI = os.environ.get('DATABASE_URL')