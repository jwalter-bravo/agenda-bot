import asyncio
import os
from datetime import datetime, timedelta
from telegram import Bot
import logging
from bot.services.tts import TTSService
from database.models import Usuario, Evento

logger = logging.getLogger(__name__)

class RecordatorioService:
    def __init__(self, bot_token, db_session):
        self.bot = Bot(token=bot_token)
        self.db = db_session
        self.tts = TTSService()
    
    async def verificar_recordatorios(self):
        """Verifica eventos próximos y envía recordatorios"""
        ahora = datetime.now()
        limite = ahora + timedelta(minutes=30)
    logger.info(f"🔍 [DEBUG] Ahora: {ahora}")
    logger.info(f"🔍 [DEBUG] Límite: {limite}")
        
        eventos = self.db.query(Evento).filter(
            Evento.fecha_hora > ahora - timedelta(minutes=5),  # ✅ CORRECTO,
            Evento.fecha_hora <= limite,
            Evento.completado == False,
            Evento.recordado == False
        ).all()
        
        for evento in eventos:
            minutos_restantes = int((evento.fecha_hora - ahora).total_seconds() / 60)
            
            if minutos_restantes <= 5:
                await self.enviar_recordatorio(evento, minutos_restantes)
    
    async def enviar_recordatorio(self, evento, minutos):
        """Envía recordatorio por texto y voz"""
        usuario = self.db.query(Usuario).filter(
            Usuario.telegram_id == evento.usuario_id
        ).first()
        
        if not usuario:
            return
        
        mensaje_texto = (
            f"⏰ **Recordatorio!**\n\n"
            f"📌 {evento.titulo}\n"
            f"🕐 Comienza en {minutos} minutos"
        )
        
        try:
            await self.bot.send_message(
                chat_id=usuario.telegram_id,
                text=mensaje_texto,
                parse_mode='Markdown'
            )
            
            if usuario.notificaciones_voz:
                texto_voz = self.tts.generar_mensaje_recordatorio(evento)
                archivo_audio = f"recordatorio_{evento.id}.mp3"
                
                await self.tts.texto_a_voz(texto_voz, archivo_audio)
                
                with open(archivo_audio, 'rb') as audio:
                    await self.bot.send_voice(
                        chat_id=usuario.telegram_id,
                        voice=audio
                    )
                
                if os.path.exists(archivo_audio):
                    os.remove(archivo_audio)
                    
            # ✅ ESTA ES LA LÍNEA CLAVE QUE FALTABA:
            evento.recordado = True
            self.db.commit()
            
            logger.info(f"✅ Recordatorio enviado para: {evento.titulo}")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            self.db.rollback()
