from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID  
import uuid
from app import bd

class Reuniao(bd.Model):
    __tablename__ = 'reuniao'
    id = bd.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    descricao = bd.Column(bd.String(255), nullable=False)
    data_criacao = bd.Column(bd.DateTime, default=datetime.now)
    finalizada = bd.Column(bd.Boolean, default=False)
    participantes = bd.relationship('Presenca', back_populates='reuniao', cascade="all, delete-orphan")
