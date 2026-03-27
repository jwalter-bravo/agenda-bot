from database.models import init_db, Evento
from config import Config

db = init_db(Config.DATABASE_URL)

eventos = db.query(Evento).filter(
    Evento.titulo.like('%Prueba recordatorio%')
).all()

for evento in eventos:
    print(f"ID: {evento.id}")
    print(f"Título: {evento.titulo}")
    print(f"Fecha: {evento.fecha_hora}")
    print(f"Completado: {evento.completado}")
    print(f"Recordado: {evento.recordado}")
    print("---")

db.close()
