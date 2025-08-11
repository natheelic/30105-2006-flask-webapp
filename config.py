import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    MYSQL_HOST = '61.19.114.86'
    MYSQL_PORT = 54000
    MYSQL_USER = 'nathee'
    MYSQL_PASSWORD = 'Root@1234'
    MYSQL_DB = 'iot_webapp'
    MYSQL_CHARSET = 'utf8mb4'
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    DEBUG = True