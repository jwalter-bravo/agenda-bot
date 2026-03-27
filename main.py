import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from bot.handlers import eventos, tareas
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
        "/semana - Ver agenda de la semana\n"
        "/tareas - Ver mis tareas pendientes\n"
        "/tarea_agregar - Agregar nueva tarea\n"
        "/stats - Ver tus estadísticas\n"
        "/voz - Activar/desactivar notificaciones de voz\n"
        "/start - Mostrar este mensaje\n\n"
        "¡Comienza agregando tu primer evento con /agregar!"
    )

async def error_handler(update: Update, context):
    logger.error(f"❌ Error: {context.error}")

def job_recordatorios():
    from database.models import init_db
    from bot.services.recordatorios import RecordatorioService
    import asyncio
    
    db = init_db(Config.DATABASE_URL)
    recordatorios = RecordatorioService(Config.BOT_TOKEN, db)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(recordatorios.verificar_recordatorios())
    finally:
        loop.close()
        db.close()

def main():
    if not Config.BOT_TOKEN:
        logger.error("❌ BOT_TOKEN no configurado")
        return
    
    logger.info(f"🤖 Iniciando AgendaBot...")
    
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(configurar_menu(application))
    
    application.add_handler(CommandHandler('start', start))
   # application.add_handler(CommandHandler('hoy', eventos.mostrar_hoy))
   # application.add_handler(CommandHandler('semana', eventos.mostrar_semana))
    application.add_handler(CommandHandler('voz', toggle_voz))
    
    application.add_handler(CommandHandler('tareas', tareas.mostrar_tareas))
    application.add_handler(CommandHandler('tarea_completar', tareas.tarea_completar))
    application.add_handler(CommandHandler('stats', tareas.mostrar_stats))
    application.add_handler(CommandHandler('buscar', tareas.buscar_tarea))
    application.add_handler(CommandHandler('exportar', tareas.exportar_datos))
    application.add_handler(CommandHandler('buscar', tareas.buscar_tarea))
    application.add_handler(CommandHandler('exportar', tareas.exportar_datos))
    application.add_handler(CommandHandler('eliminar', tareas.eliminar_tarea_start))
    
    conv_handler = ConversationHandler(
       # entry_points=[CommandHandler('agregar', eventos.agregar_evento_start)],
        states={
        #    eventos.NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, eventos.agregar_evento_nombre)],
        #    eventos.FECHA_HORA: [MessageHandler(filters.TEXT & ~filters.COMMAND, eventos.agregar_evento_fecha)],
            eventos.CATEGORIA: [CallbackQueryHandler(eventos.agregar_evento_categoria)],
            eventos.PRIORIDAD: [CallbackQueryHandler(eventos.agregar_evento_prioridad)],
            eventos.CONFIRMAR: [CallbackQueryHandler(eventos.agregar_evento_confirmar)],
        },
        fallbacks=[CommandHandler('cancelar', eventos.cancelar)]
    )
    application.add_handler(conv_handler)
    
    conv_tareas = ConversationHandler(
        entry_points=[CommandHandler('tarea_agregar', tareas.tarea_agregar_start)],
        states={
            tareas.TITULO: [MessageHandler(filters.TEXT & ~filters.COMMAND, tareas.tarea_titulo)],
            tareas.DESCRIPCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, tareas.tarea_descripcion)],
            tareas.FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, tareas.tarea_fecha)],
            tareas.CATEGORIA: [CallbackQueryHandler(tareas.tarea_categoria)],
            tareas.PRIORIDAD: [CallbackQueryHandler(tareas.tarea_prioridad)],
            tareas.CONFIRMAR: [CallbackQueryHandler(tareas.tarea_confirmar)],
        },
        fallbacks=[CommandHandler('cancelar', tareas.cancelar_tarea)],
        per_user=True,
        per_chat=True,
        per_message=False
    )
    application.add_handler(conv_tareas)
    
    # ConversationHandler para editar tareas
    conv_editar = ConversationHandler(
        entry_points=[CommandHandler('editar', tareas.editar_tarea_start)],
        states={
            tareas.EDITAR_SELECCIONAR: [CallbackQueryHandler(tareas.editar_tarea_seleccionar, pattern='^edit_')],
            tareas.EDITAR_CAMPO: [CallbackQueryHandler(tareas.editar_tarea_campo, pattern='^edit_')],
            tareas.EDITAR_VALOR: [
                CallbackQueryHandler(tareas.editar_tarea_campo, pattern='^edit_'),
                CallbackQueryHandler(tareas.editar_tarea_guardar, pattern='^prioridad_'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, tareas.editar_tarea_guardar)
            ],
        },
        fallbacks=[CommandHandler('cancelar', tareas.editar_tarea_cancelar)],
        per_user=True,
        per_chat=True,
        per_message=False
    )
    application.add_handler(conv_editar)

    
    application.add_handler(CallbackQueryHandler(tareas.tarea_completar_callback, pattern='^completar_'))
    application.add_handler(CallbackQueryHandler(tareas.eliminar_tarea_confirmar, pattern='^del_[0-9]+$'))
    application.add_handler(CallbackQueryHandler(tareas.eliminar_tarea_final, pattern='^del_(confirmar|cancel)$'))
    
    application.add_error_handler(error_handler)
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_recordatorios, 'interval', minutes=1)
    scheduler.start()
    logger.info("⏰ Servicio de recordatorios iniciado (cada 1 minuto)")
    
    logger.info("🚀 Bot iniciado. Esperando mensajes...")
    application.run_polling()

if __name__ == '__main__':
    main()

    
