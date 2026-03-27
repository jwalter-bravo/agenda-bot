from database.models import init_db, Evento
from config import Config
from datetime import datetime, timedelta

db = init_db(Config.DATABASE_URL)

ahora = datetime.now()
hoy_inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
hoy_fin = hoy_inicio + timedelta(days=1)

eventos = db.query(Evento).filter(
    Evento.fecha_hora >= hoy_inicio,
    Evento.fecha_hora <= hoy_fin
).all()

print(f"📅 Eventos de hoy ({ahora.strftime('%Y-%m-%d')}):")
print(f"Encontrados: {len(eventos)}\n")

for evento in eventos:
    print(f"ID: {evento.id}")
    print(f"Título: {evento.titulo}")
    print(f"Fecha: {evento.fecha_hora}")
    print(f"Completado: {evento.completado}")
    print(f"Recordado: {evento.recordado}")
    print("---")

if len(eventos) == 0:
    print("⚠️ NO hay eventos de hoy en la base de datos")
    print("💡 Los eventos creados en Telegram se guardan en la DB de Railway, no local")

db.close()
