from telegram import BotCommand, BotCommandScopeDefault
import logging

logger = logging.getLogger(__name__)

async def configurar_menu(application):
    """Configura el menú persistente del bot"""
    
    comandos = [
        BotCommand("start", "🏠 Iniciar el bot"),
        BotCommand("hoy", "📅 Ver agenda de hoy"),
        BotCommand("semana", "📆 Ver agenda de la semana"),
        BotCommand("agregar", "➕ Agregar nuevo evento"),
        BotCommand("tareas", "📝 Lista de tareas"),
        BotCommand("voz", "🔊 Activar/desactivar voz"),
        BotCommand("reporte", "📊 Reporte de productividad"),
    ]
    
    try:
        await application.bot.set_my_commands(comandos, scope=BotCommandScopeDefault())
        logger.info("✅ Menú de comandos configurado")
    except Exception as e:
        logger.error(f"❌ Error configurando menú: {e}")
