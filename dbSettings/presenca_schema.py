from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID  
import uuid
from app import bd
class Presenca(bd.Model):
    __tablename__ = 'presenca'
    id = bd.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = bd.Column(bd.String(100), nullable=False)
    cargo = bd.Column(bd.String(100), nullable=False)
    setor = bd.Column(bd.String(100), nullable=False)
    entrada = bd.Column(bd.DateTime, nullable=False)
    meeting_id = bd.Column(UUID(as_uuid=True), bd.ForeignKey('reuniao.id'), nullable=False)
    reuniao = bd.relationship('Reuniao', back_populates='participantes')
