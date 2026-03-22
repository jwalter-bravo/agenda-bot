import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL')
    
    # Configuración
    TIMEZONE = os.getenv('TIMEZONE', 'America/Argentina/Buenos_Aires')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Pomodoro
    POMODORO_WORK = 25
    POMODORO_BREAK = 5
