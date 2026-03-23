from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

class Prioridad(enum.Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"

class Categoria(enum.Enum):
    PERSONAL = "personal"
    LABORAL = "laboral"

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    nombre = Column(String)
    notificaciones_voz = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Evento(Base):
    __tablename__ = 'eventos'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, nullable=False)
    titulo = Column(String, nullable=False)
    descripcion = Column(Text)
    fecha_hora = Column(DateTime, nullable=False)
    duracion = Column(Integer, default=60)
    categoria = Column(Enum(Categoria))
    prioridad = Column(Enum(Prioridad))
    completado = Column(Boolean, default=False)
    recordado = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Tarea(Base):
    __tablename__ = 'tareas'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, nullable=False)
    titulo = Column(String, nullable=False)
    descripcion = Column(Text)
    fecha_limite = Column(DateTime)
    categoria = Column(Enum(Categoria))
    prioridad = Column(Enum(Prioridad))
    completado = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db(database_url):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
