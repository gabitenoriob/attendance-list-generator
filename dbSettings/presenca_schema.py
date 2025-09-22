from .database import db 

class Presenca(db.Model):
    id = db.Column(db.String(12), primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    setor = db.Column(db.String(100), nullable=False)
    entrada = db.Column(db.DateTime, nullable=False)
    meeting_id = db.Column(db.String(12), db.ForeignKey('reuniao.id'), nullable=False)
    reuniao = db.relationship('Reuniao', backref=db.backref('presenca', lazy=True))