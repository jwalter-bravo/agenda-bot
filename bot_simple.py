import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8259940032:AAGZ0MacY_A6sPVPnOPc3rr_G0rq-s8VIqw"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"✅ Recibido /start de {update.effective_user.id}")
    await update.message.reply_text("🎉 ¡Hola! El bot funciona correctamente.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"✅ Recibido mensaje: {update.message.text}")
    await update.message.reply_text(f"Recibí: {update.message.text}")

def main():
    print("🤖 Bot de prueba iniciado...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print("✅ Bot listo. Esperando mensajes...")
    app.run_polling()

if __name__ == "__main__":
    main()
