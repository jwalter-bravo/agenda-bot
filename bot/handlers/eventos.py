from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
import dateparser
from database.models import Evento, Categoria, Prioridad, init_db
from config import Config
import logging

logger = logging.getLogger(__name__)

NOMBRE, FECHA_HORA, CATEGORIA, PRIORIDAD, CONFIRMAR = range(5)

db_session = init_db(Config.DATABASE_URL)

async def agregar_evento_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📅 Vamos a agregar un evento.\n\n"
        "📝 ¿Cuál es el título del evento?"
    )
    return NOMBRE

async def agregar_evento_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['evento'] = {'titulo': update.message.text}
    await update.message.reply_text(
        "⏰ ¿Cuándo es el evento?\n\n"
        "Ejemplos:\n"
        "- Mañana a las 15:00\n"
        "- Viernes 10 de mayo 9am\n"
        "- 25/12/2024 20:00"
    )
    return FECHA_HORA

async def agregar_evento_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fecha_texto = update.message.text
    fecha_parseada = dateparser.parse(
        fecha_texto,
        settings={'PREFER_DATES_FROM': 'future', 'TIMEZONE': 'America/Argentina/Buenos_Aires'}
    )
    
    if not fecha_parseada:
        await update.message.reply_text(
            "❌ No entendí la fecha. Intenta con otro formato:\n"
            "Mañana 3pm\n"
            "Viernes 10am"
        )
        return FECHA_HORA
    
    context.user_data['evento']['fecha_hora'] = fecha_parseada
    
    keyboard = [
        [InlineKeyboardButton("📁 Personal", callback_data="personal")],
        [InlineKeyboardButton("💼 Laboral", callback_data="laboral")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("🏷️ Selecciona la categoría:", reply_markup=reply_markup)
    return CATEGORIA

async def agregar_evento_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['evento']['categoria'] = query.data
    
    keyboard = [
        [InlineKeyboardButton("🔴 Alta", callback_data="alta")],
        [InlineKeyboardButton("🟡 Media", callback_data="media")],
        [InlineKeyboardButton("🟢 Baja", callback_data="baja")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("⚡ Selecciona la prioridad:", reply_markup=reply_markup)
    return PRIORIDAD

async def agregar_evento_prioridad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['evento']['prioridad'] = query.data
    evento = context.user_data['evento']
    
    resumen = (
        f"✅ **Resumen del evento:**\n\n"
        f"📌 **Título:** {evento['titulo']}\n"
        f"📅 **Fecha:** {evento['fecha_hora'].strftime('%A %d/%m/%Y %H:%M')}\n"
        f"🏷️ **Categoría:** {evento['categoria'].capitalize()}\n"
        f"⚡ **Prioridad:** {evento['prioridad'].capitalize()}\n\n"
        f"¿Confirmar creación?"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Sí", callback_data="confirmar")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(resumen, reply_markup=reply_markup, parse_mode='Markdown')
    return CONFIRMAR

async def agregar_evento_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirmar":
        evento_data = context.user_data['evento']
        user = update.effective_user
        
        try:
            nuevo_evento = Evento(
                usuario_id=user.id,
                titulo=evento_data['titulo'],
                fecha_hora=evento_data['fecha_hora'],
                categoria=Categoria(evento_data['categoria']),
                prioridad=Prioridad(evento_data['prioridad'])
            )
            db_session.add(nuevo_evento)
            db_session.commit()
            
            await query.edit_message_text(
                f"✅ ¡Evento guardado!\n\n"
                f"📌 {evento_data['titulo']}\n"
                f"📅 {evento_data['fecha_hora'].strftime('%d/%m/%Y %H:%M')}",
                parse_mode='Markdown'
            )
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error: {e}")
            await query.edit_message_text("❌ Error al guardar.")
    else:
        await query.edit_message_text("❌ Cancelado.")
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelado.")
    context.user_data.clear()
    return ConversationHandler.END

async def mostrar_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    manana = hoy.replace(day=hoy.day + 1)
    
    eventos_hoy = db_session.query(Evento).filter(
        Evento.usuario_id == user.id,
        Evento.fecha_hora >= hoy,
        Evento.fecha_hora < manana,
        Evento.completado == False
    ).order_by(Evento.fecha_hora).all()
    
    if eventos_hoy:
        mensaje = "📅 **Agenda de Hoy**\n\n"
        for e in eventos_hoy:
            emoji = "🔴" if e.prioridad.value == "alta" else "🟡" if e.prioridad.value == "media" else "🟢"
            mensaje += f"{emoji} {e.titulo} - {e.fecha_hora.strftime('%H:%M')}\n"
        await update.message.reply_text(mensaje, parse_mode='Markdown')
    else:
        await update.message.reply_text("📅 **Agenda de Hoy**\n\n🎉 ¡No hay eventos! Usa /agregar", parse_mode='Markdown')
async def mostrar_semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los eventos de los próximos 7 días"""
    user = update.effective_user
    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    desde_la_semana = hoy
    hasta_la_semana = hoy.replace(day=hoy.day + 7)
    
    eventos_semana = db_session.query(Evento).filter(
        Evento.usuario_id == user.id,
        Evento.fecha_hora >= desde_la_semana,
        Evento.fecha_hora < hasta_la_semana,
        Evento.completado == False
    ).order_by(Evento.fecha_hora).all()
    
    if eventos_semana:
        mensaje = "📅 **Agenda de la Semana**\n\n"
        
        # Agrupar eventos por día
        eventos_por_dia = {}
        for e in eventos_semana:
            dia = e.fecha_hora.strftime('%A %d/%m')
            if dia not in eventos_por_dia:
                eventos_por_dia[dia] = []
            eventos_por_dia[dia].append(e)
        
        # Mostrar eventos agrupados
        for dia, eventos in eventos_por_dia.items():
            mensaje += f"📌 **{dia}**\n"
            for e in eventos:
                emoji = "🔴" if e.prioridad.value == "alta" else "🟡" if e.prioridad.value == "media" else "🟢"
                mensaje += f"  {emoji} {e.titulo} - {e.fecha_hora.strftime('%H:%M')}\n"
            mensaje += "\n"
        
        await update.message.reply_text(mensaje, parse_mode='Markdown')
    else:
        await update.message.reply_text("📅 **Agenda de la Semana**\n\n🎉 ¡No hay eventos! Usa /agregar", parse_mode='Markdown')        
