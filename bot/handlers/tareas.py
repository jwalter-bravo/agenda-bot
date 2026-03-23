from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from datetime import datetime
import dateparser
from database.models import Tarea, Categoria, Prioridad, init_db
from config import Config
import logging

logger = logging.getLogger(__name__)

db_session = init_db(Config.DATABASE_URL)

TITULO, DESCRIPCION, FECHA, CATEGORIA, PRIORIDAD, CONFIRMAR = range(6)

async def mostrar_tareas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra todas las tareas pendientes del usuario"""
    user = update.effective_user
    
    tareas = db_session.query(Tarea).filter(
        Tarea.usuario_id == user.id,
        Tarea.completado == False
    ).order_by(Tarea.fecha_limite).all()
    
    if tareas:
        mensaje = "📝 **Mis Tareas**\n\n"
        for i, t in enumerate(tareas, 1):
            emoji = "🔴" if t.prioridad.value == "alta" else "🟡" if t.prioridad.value == "media" else "🟢"
            estado = "⏳" if not t.completado else "✅"
            fecha = t.fecha_limite.strftime('%d/%m %H:%M') if t.fecha_limite else "Sin fecha"
            mensaje += f"{i}. {estado} {emoji} {t.titulo}\n   📅 {fecha}\n"
        
        mensaje += "\n💡 Usa /tarea_agregar para crear una nueva tarea"
        await update.message.reply_text(mensaje, parse_mode='HTML')
    else:
        await update.message.reply_text(
            "📝 **Mis Tareas**\n\n"
            "🎉 ¡No hay tareas pendientes!\n\n"
            "💡 Usa /tarea_agregar para crear una nueva tarea",
            parse_mode='Markdown'
        )

async def tarea_agregar_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de agregar una tarea"""
    await update.message.reply_text(
        "📝 Vamos a agregar una tarea.\n\n"
        "📌 ¿Cuál es el título de la tarea?"
    )
    return TITULO

async def tarea_titulo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"📝 [DIAG] Recibido título: {update.message.text}")
    context.user_data['tarea'] = {'titulo': update.message.text}
    await update.message.reply_text(
        "📄 ¿Quieres agregar una descripción? (opcional)\n\n"
        "Escribe la descripción o envía /saltar para omitir"
    )
    return DESCRIPCION

async def tarea_descripcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "/saltar":
        context.user_data['tarea']['descripcion'] = None
    else:
        context.user_data['tarea']['descripcion'] = update.message.text
    
    await update.message.reply_text(
        "⏰ ¿Cuándo es la fecha límite? (opcional)\n\n"
        "Ejemplos:\n"
        "- Mañana\n"
        "- Viernes 5pm\n"
        "- 25/12/2024\n"
        "O envía /saltar para omitir"
    )
    return FECHA

async def tarea_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "/saltar":
        context.user_data['tarea']['fecha_limite'] = None
    else:
        fecha_parseada = dateparser.parse(
            update.message.text,
            settings={'TIMEZONE': 'America/Argentina/Buenos_Aires'}
        )
        context.user_data['tarea']['fecha_limite'] = fecha_parseada
    
    keyboard = [
        [InlineKeyboardButton("📁 Personal", callback_data="personal")],
        [InlineKeyboardButton("💼 Laboral", callback_data="laboral")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("🏷 Selecciona la categoría:", reply_markup=reply_markup)
    return CATEGORIA

async def tarea_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['tarea']['categoria'] = query.data
    
    keyboard = [
        [InlineKeyboardButton("🔴 Alta", callback_data="alta")],
        [InlineKeyboardButton("🟡 Media", callback_data="media")],
        [InlineKeyboardButton("🟢 Baja", callback_data="baja")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("⚡ Selecciona la prioridad:", reply_markup=reply_markup)
    return PRIORIDAD

async def tarea_prioridad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['tarea']['prioridad'] = query.data
    tarea = context.user_data['tarea']
    
    resumen = (
        f"✅ **Resumen de la tarea:**\n\n"
        f"📌 **Título:** {tarea['titulo']}\n"
        f"📄 **Descripción:** {tarea.get('descripcion', 'Sin descripción')}\n"
        f"📅 **Fecha límite:** {tarea['fecha_limite'].strftime('%d/%m/%Y') if tarea.get('fecha_limite') else 'Sin fecha'}\n"
        f"🏷 **Categoría:** {tarea['categoria'].capitalize()}\n"
        f"⚡ **Prioridad:** {tarea['prioridad'].capitalize()}\n\n"
        f"¿Confirmar creación?"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Sí", callback_data="confirmar")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(resumen, reply_markup=reply_markup, parse_mode='Markdown')
    return CONFIRMAR

async def tarea_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirmar":
        tarea_data = context.user_data['tarea']
        user = update.effective_user
        
        try:
            nueva_tarea = Tarea(
                usuario_id=user.id,
                titulo=tarea_data['titulo'],
                descripcion=tarea_data.get('descripcion'),
                fecha_limite=tarea_data.get('fecha_limite'),
                categoria=Categoria(tarea_data['categoria']),
                prioridad=Prioridad(tarea_data['prioridad'])
            )
            db_session.add(nueva_tarea)
            db_session.commit()
            
            await query.edit_message_text(
                f"✅ ¡Tarea guardada!\n\n"
                f"📌 {tarea_data['titulo']}\n"
                f"📅 Fecha límite: {tarea_data['fecha_limite'].strftime('%d/%m/%Y') if tarea_data.get('fecha_limite') else 'Sin fecha'}",
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

async def tarea_completar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra tareas con botones para marcar como completadas"""
    user = update.effective_user
    
    tareas = db_session.query(Tarea).filter(
        Tarea.usuario_id == user.id,
        Tarea.completado == False
    ).all()
    
    if not tareas:
        await update.message.reply_text("🎉 ¡No hay tareas pendientes!")
        return
    
    keyboard = []
    for t in tareas:
        keyboard.append([InlineKeyboardButton(f"✅ {t.titulo}", callback_data=f"completar_{t.id}")])
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📝 Selecciona una tarea para marcar como completada:", reply_markup=reply_markup)

async def tarea_completar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancelar":
        await query.edit_message_text("❌ Cancelado.")
        return
    
    if query.data.startswith("completar_"):
        tarea_id = int(query.data.split("_")[1])
        tarea = db_session.query(Tarea).filter_by(id=tarea_id).first()
        
        if tarea:
            tarea.completado = True
            db_session.commit()
            await query.edit_message_text(f"✅ ¡Tarea \"{tarea.titulo}\" completada! 🎉")
        else:
            await query.edit_message_text("❌ Tarea no encontrada.")

async def cancelar_tarea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelado.")
    context.user_data.clear()
    return ConversationHandler.END

async def mostrar_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra estadísticas del usuario"""
    user = update.effective_user
    print(f"📊 [STATS] Usuario {user.id} solicitó estadísticas")
    
    try:
        tareas_completadas = db_session.query(Tarea).filter(
            Tarea.usuario_id == user.id,
            Tarea.completado == True
        ).count()
        
        tareas_pendientes = db_session.query(Tarea).filter(
            Tarea.usuario_id == user.id,
            Tarea.completado == False
        ).count()
        
        total_tareas = db_session.query(Tarea).filter(
            Tarea.usuario_id == user.id
        ).count()
        
        total_eventos = 0
        racha = 0
        
        mensaje = (
            f"📊 **Tus Estadísticas**\n\n"
            f"✅ Tareas completadas: {tareas_completadas}\n"
            f"⏳ Tareas pendientes: {tareas_pendientes}\n"
            f"📅 Eventos creados: {total_eventos}\n\n"
            f"🔥 Racha actual: {racha} días\n"
            f"🏆 Total de tareas en la historia: {total_tareas}\n\n"
            f"¡Sigue así! 💪"
        )
        
        await update.message.reply_text(mensaje, parse_mode='HTML')
        print(f"📊 [STATS] Estadísticas enviadas")
        
    except Exception as e:
        print(f"📊 [STATS] Error: {e}")
        await update.message.reply_text("❌ Error al mostrar estadísticas.")

async def eliminar_tarea_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra las tareas con botones para eliminar"""
    user = update.effective_user
    print(f"🗑 [ELIMINAR] Usuario {user.id} solicitó eliminar tarea")
    
    try:
        tareas = db_session.query(Tarea).filter(
            Tarea.usuario_id == user.id,
            Tarea.completado == False
        ).all()
        
        if not tareas:
            await update.message.reply_text("🎉 ¡No hay tareas pendientes para eliminar!")
            return
        
        mensaje = "🗑 **Selecciona la tarea a eliminar:**\n\n"
        keyboard = []
        
        for i, t in enumerate(tareas, 1):
            emoji = "🔴" if t.prioridad.value == "alta" else "🟡" if t.prioridad.value == "media" else "🟢"
            mensaje += f"{i}. {emoji} {t.titulo}\n"
            keyboard.append([InlineKeyboardButton(f"🗑 Eliminar #{i}", callback_data=f"del_{t.id}")])
        
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="del_cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='HTML')
        print(f"🗑 [ELIMINAR] Mostradas {len(tareas)} tareas para eliminar")
        
    except Exception as e:
        print(f"🗑 [ELIMINAR] Error: {e}")
        await update.message.reply_text("❌ Error al mostrar tareas.")


async def eliminar_tarea_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma la eliminación de una tarea"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "del_cancel":
        await query.edit_message_text("❌ Cancelado.")
        return
    
    if query.data.startswith("del_"):
        tarea_id = int(query.data.split("_")[1])
        tarea = db_session.query(Tarea).filter_by(id=tarea_id).first()
        
        if tarea:
            context.user_data['tarea_a_eliminar'] = tarea_id
            
            keyboard = [
                [InlineKeyboardButton("✅ Sí, eliminar", callback_data="del_confirmar")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="del_cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"⚠️ ¿Estás seguro de eliminar esta tarea?\n\n"
                f"📌 **{tarea.titulo}**\n"
                f"📅 Fecha: {tarea.fecha_limite.strftime('%d/%m/%Y') if tarea.fecha_limite else 'Sin fecha'}\n\n"
                f"Esta acción no se puede deshacer.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text("❌ Tarea no encontrada.")


async def eliminar_tarea_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Elimina la tarea confirmada"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "del_confirmar":
        tarea_id = context.user_data.get('tarea_a_eliminar')
        
        if tarea_id:
            tarea = db_session.query(Tarea).filter_by(id=tarea_id).first()
            
            if tarea:
                db_session.delete(tarea)
                db_session.commit()
                await query.edit_message_text(f"✅ Tarea \"{tarea.titulo}\" eliminada correctamente. 🗑")
                print(f"🗑 [ELIMINAR] Tarea {tarea_id} eliminada")
            else:
                await query.edit_message_text("❌ Tarea no encontrada.")
            
            context.user_data.pop('tarea_a_eliminar', None)
        else:
            await query.edit_message_text("❌ Error: No hay tarea seleccionada.")
    
    elif query.data == "del_cancel":
        await query.edit_message_text("❌ Cancelado.")
        context.user_data.pop('tarea_a_eliminar', None)

async def buscar_tarea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca tareas por texto"""
    user = update.effective_user
    query = context.args
    
    if not query:
        await update.message.reply_text(
            "🔍 **Búsqueda de Tareas**\n\n"
            "Usa: /buscar [texto]\n\n"
            "Ejemplos:\n"
            "/buscar karina\n"
            "/buscar reunion\n"
            "/buscar importante",
            parse_mode='HTML'
        )
        return
    
    search_text = ' '.join(query).lower()
    print(f"🔍 [BUSCAR] Usuario {user.id} busca: {search_text}")
    
    try:
        todas_las_tareas = db_session.query(Tarea).filter(
            Tarea.usuario_id == user.id
        ).all()
        
        resultados = []
        for t in todas_las_tareas:
            if (search_text in t.titulo.lower() or 
                (t.descripcion and search_text in t.descripcion.lower())):
                resultados.append(t)
        
        if not resultados:
            await update.message.reply_text(
                f"😕 No encontré tareas que coincidan con \"{search_text}\"\n\n"
                "💡 Prueba con otras palabras clave."
            )
            return
        
        mensaje = f"🔍 **Resultados para \"{search_text}\":**\n\n"
        mensaje += f"📊 Encontradas {len(resultados)} tarea(s)\n\n"
        
        for i, t in enumerate(resultados[:10], 1):
            emoji = "🔴" if t.prioridad.value == "alta" else "🟡" if t.prioridad.value == "media" else "🟢"
            estado = "✅" if t.completado else "⏳"
            fecha = t.fecha_limite.strftime('%d/%m %H:%M') if t.fecha_limite else "Sin fecha"
            
            mensaje += f"{i}. {estado} {emoji} **{t.titulo}**\n"
            if t.descripcion:
                desc_corta = t.descripcion[:50] + "..." if len(t.descripcion) > 50 else t.descripcion
                mensaje += f"   📄 {desc_corta}\n"
            mensaje += f"   📅 {fecha}\n\n"
        
        if len(resultados) > 10:
            mensaje += f"... y {len(resultados) - 10} resultados más\n"
        
        await update.message.reply_text(mensaje, parse_mode='HTML')
        print(f"🔍 [BUSCAR] Encontradas {len(resultados)} tareas")
        
    except Exception as e:
        print(f"🔍 [BUSCAR] Error: {e}")
        await update.message.reply_text("❌ Error al buscar tareas.")


async def buscar_tarea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca tareas por texto"""
    user = update.effective_user
    query = context.args
    
    if not query:
        await update.message.reply_text(
            "🔍 **Búsqueda de Tareas**\n\n"
            "Usa: /buscar [texto]\n\n"
            "Ejemplos:\n"
            "/buscar karina\n"
            "/buscar reunion\n"
            "/buscar importante",
            parse_mode='HTML'
        )
        return
    
    search_text = ' '.join(query).lower()
    print(f"🔍 [BUSCAR] Usuario {user.id} busca: {search_text}")
    
    try:
        todas_las_tareas = db_session.query(Tarea).filter(
            Tarea.usuario_id == user.id
        ).all()
        
        resultados = []
        for t in todas_las_tareas:
            if (search_text in t.titulo.lower() or 
                (t.descripcion and search_text in t.descripcion.lower())):
                resultados.append(t)
        
        if not resultados:
            await update.message.reply_text(
                f"😕 No encontré tareas que coincidan con \"{search_text}\"\n\n"
                "💡 Prueba con otras palabras clave."
            )
            return
        
        mensaje = f"🔍 **Resultados para \"{search_text}\":**\n\n"
        mensaje += f"📊 Encontradas {len(resultados)} tarea(s)\n\n"
        
        for i, t in enumerate(resultados[:10], 1):
            emoji = "🔴" if t.prioridad.value == "alta" else "🟡" if t.prioridad.value == "media" else "🟢"
            estado = "✅" if t.completado else "⏳"
            fecha = t.fecha_limite.strftime('%d/%m %H:%M') if t.fecha_limite else "Sin fecha"
            
            mensaje += f"{i}. {estado} {emoji} **{t.titulo}**\n"
            if t.descripcion:
                desc_corta = t.descripcion[:50] + "..." if len(t.descripcion) > 50 else t.descripcion
                mensaje += f"   📄 {desc_corta}\n"
            mensaje += f"   📅 {fecha}\n\n"
        
        if len(resultados) > 10:
            mensaje += f"... y {len(resultados) - 10} resultados más\n"
        
        await update.message.reply_text(mensaje, parse_mode='HTML')
        print(f"🔍 [BUSCAR] Encontradas {len(resultados)} tareas")
        
    except Exception as e:
        print(f"🔍 [BUSCAR] Error: {e}")
        await update.message.reply_text("❌ Error al buscar tareas.")


# Estados para el ConversationHandler de editar
EDITAR_SELECCIONAR = 0
EDITAR_CAMPO = 1
EDITAR_VALOR = 2



# Estados para el ConversationHandler de editar
EDITAR_SELECCIONAR = 0
EDITAR_CAMPO = 1
EDITAR_VALOR = 2

async def editar_tarea_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de edición"""
    user = update.effective_user
    print(f"✏️ [EDITAR] Usuario {user.id} inicia edición")
    
    try:
        tareas = db_session.query(Tarea).filter(
            Tarea.usuario_id == user.id,
            Tarea.completado == False
        ).all()
        
        if not tareas:
            await update.message.reply_text("🎉 ¡No hay tareas pendientes para editar!")
            return ConversationHandler.END
        
        mensaje = "✏️ **Selecciona la tarea a editar:**\n\n"
        keyboard = []
        
        for i, t in enumerate(tareas, 1):
            emoji = "🔴" if t.prioridad.value == "alta" else "🟡" if t.prioridad.value == "media" else "🟢"
            mensaje += f"{i}. {emoji} {t.titulo}\n"
            keyboard.append([InlineKeyboardButton(f"✏️ Editar #{i}", callback_data=f"edit_{t.id}")])
        
        keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="edit_cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='HTML')
        return EDITAR_SELECCIONAR
        
    except Exception as e:
        print(f"✏️ [EDITAR] Error: {e}")
        await update.message.reply_text("❌ Error al iniciar edición.")
        return ConversationHandler.END


async def editar_tarea_seleccionar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra opciones de qué campo editar"""
    query = update.callback_query
    await query.answer()
    
    print(f"✏️ [DEBUG] Callback recibido: {query.data}")
    print(f"✏️ [DEBUG] user_data: {context.user_data}")
    
    if query.data == "edit_cancel":
        await query.edit_message_text("❌ Cancelado.")
        return ConversationHandler.END
    
    if query.data.startswith("edit_"):
        tarea_id = int(query.data.split("_")[1])
        tarea = db_session.query(Tarea).filter_by(id=tarea_id).first()
        
        if tarea:
            context.user_data['tarea_a_editar'] = tarea_id
            
            keyboard = [
                [InlineKeyboardButton("📝 Título", callback_data="edit_titulo")],
                [InlineKeyboardButton("📄 Descripción", callback_data="edit_descripcion")],
                [InlineKeyboardButton("📅 Fecha límite", callback_data="edit_fecha")],
                [InlineKeyboardButton("🔴 Prioridad", callback_data="edit_prioridad")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="edit_cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✏️ **Editando:** {tarea.titulo}\n\n"
                f"📄 Descripción: {tarea.descripcion or 'Sin descripción'}\n"
                f"📅 Fecha: {tarea.fecha_limite.strftime('%d/%m/%Y %H:%M') if tarea.fecha_limite else 'Sin fecha'}\n"
                f"🔴 Prioridad: {tarea.prioridad.value}\n\n"
                f"¿Qué deseas modificar?",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return EDITAR_CAMPO
        else:
            await query.edit_message_text("❌ Tarea no encontrada.")
            return ConversationHandler.END


async def editar_tarea_campo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa la selección del campo a editar"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "edit_cancel":
        await query.edit_message_text("❌ Cancelado.")
        context.user_data.pop('tarea_a_editar', None)
        return ConversationHandler.END
    
    tarea_id = context.user_data.get('tarea_a_editar')
    if not tarea_id:
        await query.edit_message_text("❌ Error: No hay tarea seleccionada.")
        return ConversationHandler.END
    
    campo = query.data.replace("edit_", "")
    context.user_data['campo_a_editar'] = campo
    
    if campo == "titulo":
        await query.edit_message_text("📝 **Nuevo título:**\n\nEscribe el nuevo título:")
    elif campo == "descripcion":
        await query.edit_message_text("📄 **Nueva descripción:**\n\nEscribe la nueva descripción (o /saltar para quitarla):")
    elif campo == "fecha":
        await query.edit_message_text("📅 **Nueva fecha límite:**\n\nEjemplos:\n- Mañana\n- Viernes 5pm\n- 25/12/2024\n\nO envía /saltar para quitar la fecha:")
    elif campo == "prioridad":
        keyboard = [
            [InlineKeyboardButton("🔴 Alta", callback_data="prioridad_alta")],
            [InlineKeyboardButton("🟡 Media", callback_data="prioridad_media")],
            [InlineKeyboardButton("🟢 Baja", callback_data="prioridad_baja")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="edit_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🔴 **Selecciona la prioridad:**",
            reply_markup=reply_markup
        )
        return EDITAR_VALOR
    
    return EDITAR_VALOR


async def editar_tarea_guardar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guarda los cambios en la tarea"""
    user = update.effective_user
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        if query.data == "edit_cancel":
            await query.edit_message_text("❌ Cancelado.")
            context.user_data.pop('tarea_a_editar', None)
            context.user_data.pop('campo_a_editar', None)
            return ConversationHandler.END
        
        if query.data.startswith("prioridad_"):
            nuevo_valor = query.data.replace("prioridad_", "")
            campo = "prioridad"
        else:
            await query.edit_message_text("❌ Opción no válida.")
            return ConversationHandler.END
    else:
        texto = update.message.text
        campo = context.user_data.get('campo_a_editar')
        nuevo_valor = texto
    
    tarea_id = context.user_data.get('tarea_a_editar')
    if not tarea_id:
        await update.message.reply_text("❌ Error: No hay tarea seleccionada.")
        return ConversationHandler.END
    
    try:
        tarea = db_session.query(Tarea).filter_by(id=tarea_id).first()
        
        if not tarea:
            await update.message.reply_text("❌ Tarea no encontrada.")
            return ConversationHandler.END
        
        if campo == "titulo":
            tarea.titulo = nuevo_valor
        elif campo == "descripcion":
            if texto == "/saltar":
                tarea.descripcion = None
            else:
                tarea.descripcion = nuevo_valor
        elif campo == "fecha":
            if texto == "/saltar":
                tarea.fecha_limite = None
            else:
                from datetime import datetime, timedelta
                if texto.lower() == "mañana":
                    tarea.fecha_limite = datetime.now() + timedelta(days=1)
                else:
                    try:
                        tarea.fecha_limite = datetime.strptime(texto, "%d/%m/%Y")
                    except:
                        tarea.fecha_limite = datetime.now() + timedelta(days=1)
        elif campo == "prioridad":
            from database.models import Prioridad
            tarea.prioridad = Prioridad(nuevo_valor)
        
        db_session.commit()
        
        await update.message.reply_text(
            f"✅ **Tarea actualizada correctamente.**\n\n"
            f"📌 {tarea.titulo}\n"
            f"📅 {tarea.fecha_limite.strftime('%d/%m/%Y') if tarea.fecha_limite else 'Sin fecha'}",
            parse_mode='HTML'
        )
        print(f"✏️ [EDITAR] Tarea {tarea_id} actualizada")
        
        context.user_data.pop('tarea_a_editar', None)
        context.user_data.pop('campo_a_editar', None)
        return ConversationHandler.END
        
    except Exception as e:
        print(f"✏️ [EDITAR] Error al guardar: {e}")
        await update.message.reply_text("❌ Error al guardar cambios.")
        return ConversationHandler.END


async def editar_tarea_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la edición"""
    context.user_data.pop('tarea_a_editar', None)
    context.user_data.pop('campo_a_editar', None)
    await update.message.reply_text("❌ Cancelado.")
    return ConversationHandler.END


async def exportar_datos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exporta las tareas del usuario a un archivo"""
    user = update.effective_user
    print(f"📥 [EXPORTAR] Usuario {user.id} solicitó exportar datos")
    
    try:
        # Obtener todas las tareas del usuario
        tareas = db_session.query(Tarea).filter(
            Tarea.usuario_id == user.id
        ).order_by(Tarea.fecha_limite).all()
        
        if not tareas:
            await update.message.reply_text(
                "📊 **Exportar Datos**\n\n"
                "🎉 ¡No tienes tareas para exportar!\n\n"
                "💡 Agrega algunas tareas con /tarea_agregar"
            )
            return
        
        # Crear contenido del archivo
        from datetime import datetime
        fecha_exportacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        contenido = f"=== EXPORTACIÓN DE TAREAS ===\n"
        contenido += f"Usuario ID: {user.id}\n"
        contenido += f"Fecha de exportación: {fecha_exportacion}\n"
        contenido += f"Total de tareas: {len(tareas)}\n"
        contenido += "=" * 40 + "\n\n"
        
        # Contadores
        completadas = 0
        pendientes = 0
        
        for i, t in enumerate(tareas, 1):
            estado = "✅ COMPLETADA" if t.completado else "⏳ PENDIENTE"
            if t.completado:
                completadas += 1
            else:
                pendientes += 1
            
            prioridad = t.prioridad.value.upper()
            fecha = t.fecha_limite.strftime("%d/%m/%Y %H:%M") if t.fecha_limite else "Sin fecha"
            
            contenido += f"[{i}] {t.titulo}\n"
            contenido += f"    Estado: {estado}\n"
            contenido += f"    Prioridad: {prioridad}\n"
            contenido += f"    Fecha límite: {fecha}\n"
            if t.descripcion:
                contenido += f"    Descripción: {t.descripcion}\n"
            contenido += "\n"
        
        # Resumen
        contenido += "=" * 40 + "\n"
        contenido += f"RESUMEN:\n"
        contenido += f"  ✅ Tareas completadas: {completadas}\n"
        contenido += f"  ⏳ Tareas pendientes: {pendientes}\n"
        contenido += f"  📊 Total: {len(tareas)}\n"
        contenido += "=" * 40 + "\n"
        contenido += f"\nGenerado por AgendaBot 🤖"
        
        # Guardar archivo temporal
        from datetime import datetime
        fecha_archivo = datetime.now().strftime("%Y-%m-%d")
        nombre_archivo = f"/tmp/tareas_{user.id}_{fecha_archivo}.txt"
        
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(contenido.replace("\\n", "\n"))
        
        # Enviar archivo
        with open(nombre_archivo, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"mis_tareas_{fecha_archivo}.txt",
                caption=f"📊 **Tus tareas exportadas**\n\n📄 {len(tareas)} tarea(s)\n✅ {completadas} completadas\n⏳ {pendientes} pendientes",
                parse_mode='HTML'
            )
        
        print(f"📥 [EXPORTAR] Archivo enviado a usuario {user.id}")
        
        # Limpiar archivo temporal
        import os
        os.remove(nombre_archivo)
        
    except Exception as e:
        print(f"📥 [EXPORTAR] Error: {e}")
        await update.message.reply_text("❌ Error al exportar datos.")
