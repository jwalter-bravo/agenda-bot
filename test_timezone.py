from datetime import datetime, timedelta, timezone
import pytz
from database.models import init_db, Evento
from config import Config

# Inicializar DB
db = init_db(Config.DATABASE_URL)

# Crear evento para DENTRO DE 5 MINUTOS (en UTC)
ahora_utc = datetime.now(timezone.utc)
evento_utc = ahora_utc + timedelta(minutes=5)

print(f"⏰ Hora actual UTC: {ahora_utc}")
print(f"📅 Evento programado UTC: {evento_utc}")

evento = Evento(
    titulo='🧪 PRUEBA TIMEZONE FIX',
    fecha_hora=evento_utc,
    usuario_id=1692734223,
    categoria='PERSONAL',
    prioridad='ALTA',
    recordado=False
)

db.add(evento)
db.commit()

print(f"✅ Evento creado en Railway DB")
print(f"🔍 ID: {evento.id}")
print(f"⏳ El recordatorio debería llegar en ~5 minutos")

db.close()
