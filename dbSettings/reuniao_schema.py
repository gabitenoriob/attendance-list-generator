from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID  
import uuid
from app import db

class Reuniao(db.Model):
    __tablename__ = 'reuniao'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    descricao = db.Column(db.String(255), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    finalizada = db.Column(db.Boolean, default=False)
    participantes = db.relationship('Presenca', back_populates='reuniao', cascade="all, delete-orphan")
