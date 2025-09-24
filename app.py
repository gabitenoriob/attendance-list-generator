from flask import Flask, jsonify, render_template, request, send_file, redirect, url_for
import qrcode
import uuid
import csv
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import base64
from io import BytesIO

from sqlalchemy import text
from dbSettings.presenca_schema import Presenca
from dbSettings.reuniao_schema import Reuniao
from dbSettings.database import db
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
db.init_app(app)
with app.app_context():
    db.create_all()

def gerar_qrcode_base64(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_b64}"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        descricao = request.form.get("descricao", "Reunião sem descrição")
        
        nova_reuniao = Reuniao(
            id= str(uuid.uuid4()),
            descricao=descricao,
            data_criacao=datetime.now()
        )
        db.session.add(nova_reuniao)
        db.session.commit()
        
        url = url_for('checkin', meeting_id=nova_reuniao.id, _external=True)
        qrcode_b64 = gerar_qrcode_base64(url)
        
        return render_template("admin.html", meeting_id=nova_reuniao.id, descricao=descricao, qrcode=qrcode_b64)
    
    reunioes = db.session.execute(db.select(Reuniao)).scalars().all()
    
    return render_template("index.html", reunioes=reunioes)

@app.route("/checkin/<meeting_id>", methods=["GET", "POST"])
def checkin(meeting_id):
    reuniao_info = db.get_or_404(Reuniao, meeting_id)

    if request.method == "POST":
        nome = request.form.get("nome", "N/A")
        cargo = request.form.get("cargo", "N/A")
        setor = request.form.get("setor", "N/A")
        
        nova_presenca = Presenca(
            id=str(uuid.uuid4()),
            nome=nome,
            cargo=cargo,
            setor=setor,
            entrada=datetime.now(),
            meeting_id=meeting_id
        )
        db.session.add(nova_presenca)
        db.session.commit()
        
        return render_template("success.html", nome=nome, meeting_id=meeting_id)

    return render_template("checkin.html", meeting_id=meeting_id, descricao=reuniao_info.descricao)

@app.route("/download/<meeting_id>")
def download(meeting_id):
    reuniao_info = db.get_or_404(Reuniao, meeting_id)
    
    presencas = db.session.execute(db.select(Presenca).filter_by(meeting_id=meeting_id)).scalars().all()

    filename = f"presencas_reuniao_{meeting_id}.csv"
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "nome", "cargo", "setor", "entrada", "meeting_id", "descricao_reuniao"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for p in presencas:
            writer.writerow({
                "id": p.id,
                "nome": p.nome,
                "cargo": p.cargo,
                "setor": p.setor,
                "entrada": p.entrada.strftime("%d-%m-%Y %H:%M:%S"),
                "meeting_id": p.meeting_id,
                "descricao_reuniao": reuniao_info.descricao
            })
    
    return send_file(filename, as_attachment=True)
@app.route("/corrigir", methods=["GET"])
def corrigir_colunas():
    queries = [
        "ALTER TABLE presenca DROP CONSTRAINT IF EXISTS presenca_meeting_id_fkey",
        "ALTER TABLE reuniao ALTER COLUMN id TYPE UUID USING id::uuid",
        "ALTER TABLE presenca ALTER COLUMN meeting_id TYPE UUID USING meeting_id::uuid",
        "ALTER TABLE presenca ADD CONSTRAINT presenca_meeting_id_fkey FOREIGN KEY (meeting_id) REFERENCES reuniao(id)"
    ]
    try:
        with db.engine.begin() as conn: 
            for q in queries:
                conn.execute(text(q))
        return jsonify({"status": "sucesso", "mensagem": "Colunas ajustadas com sucesso!"}), 200
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500
