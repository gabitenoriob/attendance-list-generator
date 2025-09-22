from flask import Flask, render_template, request, send_file, redirect, url_for
import qrcode
import uuid
import csv
from datetime import datetime
import os
import base64
from io import BytesIO

app = Flask(__name__)

MEETINGS_CSV = "data/reunioes.csv"
PRESENCA_CSV = "data/registros_presenca.csv"

os.makedirs('data', exist_ok=True)
os.makedirs('templates', exist_ok=True)

def salvar_reuniao_csv(meeting_id, descricao):
    with open(MEETINGS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([meeting_id, descricao, datetime.now().strftime("%d-%m-%Y %H:%M:%S")])

def carregar_reunioes():
    reunioes = []
    if os.path.exists(MEETINGS_CSV):
        with open(MEETINGS_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    reunioes.append({"id": row[0], "descricao": row[1], "data_criacao": row[2] if len(row) > 2 else "N/A"})
    return reunioes

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
        meeting_id = str(uuid.uuid4())[:8]
        salvar_reuniao_csv(meeting_id, descricao)
        url = url_for('checkin', meeting_id=meeting_id, _external=True)
        qrcode_b64 = gerar_qrcode_base64(url)
        return render_template("admin.html", meeting_id=meeting_id, descricao=descricao, qrcode=qrcode_b64)
    
    reunioes = carregar_reunioes()
    return render_template("index.html", reunioes=reunioes)

@app.route("/checkin/<meeting_id>", methods=["GET", "POST"])
def checkin(meeting_id):
    reunioes = carregar_reunioes()
    meeting_info = next((item for item in reunioes if item["id"] == meeting_id), None)

    if not meeting_info:
        return "Reunião não encontrada!", 404

    if request.method == "POST":
        nome = request.form.get("nome", "N/A")
        cargo = request.form.get("cargo", "N/A")
        setor = request.form.get("setor", "N/A")
        
        entrada = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        with open(PRESENCA_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([nome, cargo, setor, entrada, meeting_id, meeting_info["descricao"]])
        
        return render_template("success.html", nome=nome, meeting_id=meeting_id)

    return render_template("checkin.html", meeting_id=meeting_id, descricao=meeting_info["descricao"])

@app.route("/download/<meeting_id>")
def download(meeting_id):
    filename = f"presencas_reuniao_{meeting_id}.csv"
    with open(PRESENCA_CSV, "r", encoding="utf-8") as f_in, open(filename, "w", newline="", encoding="utf-8") as f_out:
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)
        writer.writerow(["Nome", "Cargo", "Setor", "Entrada", "ID Reunião", "Descrição"]) # Cabeçalho
        for row in reader:
            if len(row) > 4 and row[4] == meeting_id:
                writer.writerow(row)
    
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)