import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from bot.handlers import eventos
from bot.handlers.config import toggle_voz
from bot.handlers.menu import configurar_menu
from config import Config
from bot.services.recordatorios import RecordatorioService
from apscheduler.schedulers.background import BackgroundScheduler
from database.models import init_db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context):
    logger.info(f"📨 Recibido /start de {update.effective_user.id}")
    await update.message.reply_text(
        "🎉 ¡Bienvenido a AgendaBot!\n\n"
        "Comandos disponibles:\n"
        "/agregar - Crear un nuevo evento\n"
        "/hoy - Ver agenda de hoy\n"
        "/voz - Activar/desactivar notificaciones de voz\n"
        "/start - Mostrar este mensaje\n\n"
        "¡Comienza agregando tu primer evento con /agregar!"
    )

async def error_handler(update: Update, context):
    logger.error(f"❌ Error: {context.error}")

def main():
    if not Config.BOT_TOKEN:
        logger.error("❌ BOT_TOKEN no configurado")
        return
    
    logger.info(f"🤖 Iniciando AgendaBot...")
    
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Configurar menú persistente
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(configurar_menu(application))
    
    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('hoy', eventos.mostrar_hoy))
    application.add_handler(CommandHandler('voz', toggle_voz))
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('agregar', eventos.agregar_evento_start)],
        states={
            eventos.NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, eventos.agregar_evento_nombre)],
            eventos.FECHA_HORA: [MessageHandler(filters.TEXT & ~filters.COMMAND, eventos.agregar_evento_fecha)],
            eventos.CATEGORIA: [CallbackQueryHandler(eventos.agregar_evento_categoria)],
            eventos.PRIORIDAD: [CallbackQueryHandler(eventos.agregar_evento_prioridad)],
            eventos.CONFIRMAR: [CallbackQueryHandler(eventos.agregar_evento_confirmar)],
        },
        fallbacks=[CommandHandler('cancelar', eventos.cancelar)]
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    # Iniciar recordatorios
    db_session = init_db(Config.DATABASE_URL)
    recordatorios = RecordatorioService(Config.BOT_TOKEN, db_session)
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: asyncio.run(recordatorios.verificar_recordatorios()),
        'interval',
        minutes=1
    )
    scheduler.start()
    
    logger.info("🚀 Bot iniciado. Esperando mensajes...")
    application.run_polling()

if __name__ == '__main__':
    main()
