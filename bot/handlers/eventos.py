# bot/handlers/eventos.py
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, timezone
import pytz
import logging

logger = logging.getLogger(__name__)

# Estados del ConversationHandler
TITULO, FECHA, HORA, CATEGORIA, PRIORIDAD, CONFIRMAR = range(6)

# Datos temporales del evento
evento_temp = {}

def convertir_a_utc(fecha_argentina):
    """Convierte fecha de Argentina a UTC"""
    ba_tz = pytz.timezone('America/Argentina/Buenos_Aires')
    fecha_local = ba_tz.localize(fecha_argentina)
    fecha_utc = fecha_local.astimezone(timezone.utc)
    return fecha_utc.replace(tzinfo=None)  # Guardar sin timezone info

async def inicio_agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de agregar evento"""
    evento_temp.clear()
    await update.message.reply_text(
        "📝 *Nuevo Evento*\n\n"
        "Por favor, ingresá el título del evento:",
        parse_mode='Markdown'
    )
    return TITULO

async def recibir_titulo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el título del evento"""
    evento_temp['titulo'] = update.message.text
    await update.message.reply_text(
        "📅 Ahora ingresá la fecha (ej: hoy, mañana, 27/03):"
    )
    return FECHA

async def recibir_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe y procesa la fecha"""
    texto = update.message.text.lower()
    ahora_ba = datetime.now(pytz.timezone('America/Argentina/Buenos_Aires'))
    
    if texto == 'hoy':
        fecha = ahora_ba.date()
    elif texto == 'mañana':
        from datetime import timedelta
        fecha = (ahora_ba + timedelta(days=1)).date()
    else:
        try:
            partes = texto.split('/')
            fecha = datetime(ahora_ba.year, int(partes[1]), int(partes[0])).date()
        except:
            await update.message.reply_text("❌ Fecha inválida. Usá formato DD/MM o 'hoy'/'mañana':")
            return FECHA
    
    evento_temp['fecha'] = fecha
    await update.message.reply_text(
        "🕐 Ahora ingresá la hora (ej: 15:00):"
    )
    return HORA

async def recibir_hora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la hora y convierte a UTC"""
    try:
        partes = update.message.text.split(':')
        hora = datetime.combine(
            evento_temp['fecha'],
            datetime.strptime(f"{partes[0]}:{partes[1]}", "%H:%M").time()
        )
        
        # ✅ CONVERTIR A UTC ANTES DE GUARDAR
        fecha_utc = convertir_a_utc(hora)
        evento_temp['fecha_hora_utc'] = fecha_utc
        
        await update.message.reply_text(
            "🔖 Categorías disponibles:\n"
            "• PERSONAL\n"
            "• LABORAL\n\n"
            "Elegí una:"
        )
        return CATEGORIA
    except:
        await update.message.reply_text("❌ Hora inválida. Usá formato HH:MM:")
        return HORA

async def recibir_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la categoría"""
    categoria = update.message.text.upper()
    if categoria not in ['PERSONAL', 'LABORAL']:
        await update.message.reply_text("❌ Categoría inválida. Elegí PERSONAL o LABORAL:")
        return CATEGORIA
    
    evento_temp['categoria'] = categoria
    await update.message.reply_text(
        "⚡ Prioridades disponibles:\n"
        "• ALTA\n"
        "• MEDIA\n"
        "• BAJA\n\n"
        "Elegí una:"
    )
    return PRIORIDAD

async def recibir_prioridad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la prioridad"""
    prioridad = update.message.text.upper()
    if prioridad not in ['ALTA', 'MEDIA', 'BAJA']:
        await update.message.reply_text("❌ Prioridad inválida. Elegí ALTA, MEDIA o BAJA:")
        return PRIORIDAD
    
    evento_temp['prioridad'] = prioridad
    
    # Mostrar resumen
    ba_tz = pytz.timezone('America/Argentina/Buenos_Aires')
    fecha_arg = evento_temp['fecha_hora_utc'].replace(tzinfo=timezone.utc).astimezone(ba_tz)
    
    await update.message.reply_text(
        f"📋 *Resumen del Evento:*\n\n"
        f"📌 Título: {evento_temp['titulo']}\n"
        f"📅 Fecha: {fecha_arg.strftime('%d/%m/%Y %H:%M')} (hora Argentina)\n"
        f"🔖 Categoría: {evento_temp['categoria']}\n"
        f"⚡ Prioridad: {evento_temp['prioridad']}\n\n"
        f"¿Confirmás? (Sí/No):",
        parse_mode='Markdown'
    )
    return CONFIRMAR

async def confirmar_evento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma y guarda el evento"""
    if update.message.text.lower() not in ['si', 'sí', 'yes']:
        await update.message.reply_text("❌ Evento cancelado.")
        return ConversationHandler.END
    
    try:
        from database.models import Evento
        
        evento = Evento(
            titulo=evento_temp['titulo'],
            fecha_hora=evento_temp['fecha_hora_utc'],  # ✅ Guardar en UTC
            usuario_id=update.message.from_user.id,
            categoria=evento_temp['categoria'],
            prioridad=evento_temp['prioridad'],
            recordado=False
        )
        
        context.bot_data['db'].add(evento)
        context.bot_data['db'].commit()
        
        await update.message.reply_text(
            "✅ *¡Evento guardado exitosamente!*\n\n"
            "Te enviaré un recordatorio 30 minutos antes.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"❌ Error al guardar evento: {e}")
        await update.message.reply_text("❌ Error al guardar el evento. Intentá de nuevo.")
    
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela el proceso"""
    evento_temp.clear()
    await update.message.reply_text("❌ Operación cancelada.")
    return ConversationHandler.END
