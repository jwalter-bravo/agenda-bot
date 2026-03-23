import asyncio
from datetime import datetime, timedelta
from telegram import Bot
import logging
from bot.services.tts import TTSService

logger = logging.getLogger(__name__)

class RecordatorioService:
    def __init__(self, bot_token, db_session):
        self.bot = Bot(token=bot_token)
        self.db = db_session
        self.tts = TTSService()
    
    async def verificar_recordatorios(self):
        """Verifica eventos próximos y envía recordatorios"""
        ahora = datetime.now()
        
        # Buscar eventos en los próximos 30 minutos
        limite = ahora + timedelta(minutes=30)
        
        from database.models import Evento
        eventos = self.db.query(Evento).filter(
            Evento.fecha_hora > ahora,
            Evento.fecha_hora <= limite,
            Evento.completado == False
        ).all()
        
        for evento in eventos:
            # Calcular minutos restantes
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
        
        # Mensaje de texto
        mensaje_texto = (
            f"⏰ **Recordatorio!**\n\n"
            f"📌 {evento.titulo}\n"
            f"🕐 Comienza en {minutos} minutos"
        )
        
        try:
            # Enviar mensaje de texto
            await self.bot.send_message(
                chat_id=usuario.telegram_id,
                text=mensaje_texto,
                parse_mode='Markdown'
            )
            
            # Enviar mensaje de voz si está activado
            if usuario.notificaciones_voz:
                texto_voz = self.tts.generar_mensaje_recordatorio(evento)
                archivo_audio = f"recordatorio_{evento.id}.mp3"
                
                await self.tts.texto_a_voz(texto_voz, archivo_audio)
                
                with open(archivo_audio, 'rb') as audio:
                    await self.bot.send_voice(
                        chat_id=usuario.telegram_id,
                        voice=audio
                    )
                
                # Limpiar archivo temporal
                import os
                if os.path.exists(archivo_audio):
                    os.remove(archivo_audio)
                    
            logger.info(f"Recordatorio enviado para: {evento.titulo}")
            
        except Exception as e:
            logger.error(f"Error enviando recordatorio: {e}")
