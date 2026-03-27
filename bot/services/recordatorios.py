# bot/services/recordatorios.py
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import pytz

logger = logging.getLogger(__name__)

class RecordatorioService:
    def __init__(self, bot, db: Session):
        self.bot = bot
        self.db = db
    
    async def verificar_recordatorios(self):
        """Verifica y envía recordatorios de eventos próximos"""
        try:
            # ✅ USAR UTC SIEMPRE (Railway usa UTC)
            ahora_utc = datetime.now(timezone.utc)
            desde = ahora_utc
            hasta = ahora_utc + timedelta(minutes=30)  # Ventana de 30 minutos
            
            logger.info(f"🔍 Buscando eventos entre {desde} y {hasta}")
            
            # Importar Evento aquí para evitar circular imports
            from database.models import Evento
            
            # Buscar eventos en el rango de tiempo (en UTC)
            eventos = self.db.query(Evento).filter(
                Evento.fecha_hora >= desde,
                Evento.fecha_hora <= hasta,
                Evento.recordado == False
            ).all()
            
            logger.info(f"📊 Eventos encontrados: {len(eventos)}")
            
            for evento in eventos:
                await self.enviar_recordatorio(evento)
                evento.recordado = True
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"❌ Error en verificar_recordatorios: {e}")
            self.db.rollback()
    
    async def enviar_recordatorio(self, evento):
        """Envía recordatorio de un evento"""
        try:
            # Convertir de UTC a Argentina para mostrar
            ba_tz = pytz.timezone('America/Argentina/Buenos_Aires')
            if evento.fecha_hora.tzinfo is None:
                fecha_utc = evento.fecha_hora.replace(tzinfo=timezone.utc)
            else:
                fecha_utc = evento.fecha_hora
            fecha_arg = fecha_utc.astimezone(ba_tz)
            
            mensaje = (
                f"🔔 *Recordatorio:*\n\n"
                f"📌 *{evento.titulo}*\n"
                f"📅 Fecha: {fecha_arg.strftime('%d/%m/%Y %H:%M')} (hora Argentina)\n"
                f"🔖 Categoría: {evento.categoria}\n"
                f"⚡ Prioridad: {evento.prioridad}"
            )
            
            await self.bot.send_message(
                chat_id=evento.usuario_id,
                text=mensaje,
                parse_mode='Markdown'
            )
            
            logger.info(f"✅ Recordatorio enviado a usuario {evento.usuario_id}")
            
        except Exception as e:
            logger.error(f"❌ Error al enviar recordatorio: {e}")
