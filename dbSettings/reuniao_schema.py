from .database import db 

class Reuniao(db.Model):
    id = db.Column(db.String(12), primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    data_criacao = db.Column(db.String(200), nullable=False)