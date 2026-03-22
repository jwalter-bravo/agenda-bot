from telegram import Update
from telegram.ext import ContextTypes
from database.models import Usuario, init_db
from config import Config
import logging

logger = logging.getLogger(__name__)

db_session = init_db(Config.DATABASE_URL)

async def toggle_voz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activa o desactiva las notificaciones de voz"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    usuario = db_session.query(Usuario).filter(Usuario.telegram_id == user_id).first()
    
    if not usuario:
        usuario = Usuario(
            telegram_id=user_id,
            username=username,
            nombre=update.effective_user.first_name
        )
        db_session.add(usuario)
        db_session.commit()
    
    usuario.notificaciones_voz = not usuario.notificaciones_voz
    db_session.commit()
    
    estado = "activadas" if usuario.notificaciones_voz else "desactivadas"
    await update.message.reply_text(f"🔊 Notificaciones de voz {estado}")
