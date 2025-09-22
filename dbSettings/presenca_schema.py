from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID  
import uuid
from .database import db
class Presenca(db.Model):
    __tablename__ = 'presenca'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    setor = db.Column(db.String(100), nullable=False)
    entrada = db.Column(db.DateTime, nullable=False)
    meeting_id = db.Column(UUID(as_uuid=True), db.ForeignKey('reuniao.id'), nullable=False)
    reuniao = db.relationship('Reuniao', backref=db.backref('presenca', lazy=True))