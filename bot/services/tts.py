import edge_tts
import asyncio
import os

class TTSService:
    def __init__(self, voice='es-AR-ElenaNeural'):
        """
        Voces disponibles en español:
        - es-AR-ElenaNeural (argentina, femenina)
        - es-ES-ElviraNeural (españa, femenina)
        - es-MX-DaliaNeural (mexicana, femenina)
        - es-ES-AlvaroNeural (españa, masculino)
        """
        self.voice = voice
    
    async def texto_a_voz(self, texto, archivo_salida='temp.mp3'):
        """Convierte texto a archivo de audio"""
        try:
            communicate = edge_tts.Communicate(texto, self.voice)
            await communicate.save(archivo_salida)
            return archivo_salida
        except Exception as e:
            print(f"Error en TTS: {e}")
            return None
    
    def generar_mensaje_recordatorio(self, evento):
        """Genera mensaje de voz para recordatorio"""
        hora = evento.fecha_hora.strftime('%H:%M')
        titulo = evento.titulo
        prioridad = evento.prioridad.value
        
        if prioridad == 'alta':
            return f"¡Atención! Recordatorio importante. {titulo} en {hora}."
        elif prioridad == 'media':
            return f"Recordatorio: {titulo} en {hora}."
        else:
            return f"Recordatorio: {titulo} en {hora}. Tómalo con calma."
