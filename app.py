import uuid
from datetime import datetime, timezone
import qrcode
import io
import base64
import os
import csv
from flask import Flask, request, render_template, url_for, flash, redirect, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# --- Dependências para o envio de e-mail ---
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- Configuração da Aplicação Flask ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '8b1ccb67567b424dd1823732035005f5')

# --- Configuração de Banco de Dados mais Resiliente ---
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    if 'sslmode' not in database_url:
        database_url += "?sslmode=require"
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Modelos do Banco de Dados ---
class Reuniao(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    descricao = db.Column(db.String(200), nullable=False)
    data_criacao = db.Column(db.DateTime, nullable=False, default= datetime.now(timezone.utc))
    finalizada = db.Column(db.Boolean, default=False)
    participantes = db.relationship('Presenca', back_populates='reuniao', cascade="all, delete-orphan")

class Presenca(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100))
    setor = db.Column(db.String(100))
    # Usar UTC para timestamps no servidor é a melhor prática
    entrada = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    meeting_id = db.Column(db.String(36), db.ForeignKey('reuniao.id'), nullable=False)
    reuniao = db.relationship('Reuniao', back_populates='participantes')


with app.app_context():
    db.create_all()

# --- Funções Auxiliares ---
def _gerar_csv_content(reuniao):
    """Função interna para gerar o conteúdo de um CSV a partir de uma reunião."""
    output = io.StringIO()
    fieldnames = ["nome", "cargo", "setor", "hora", "reuniao"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for p in reuniao.participantes:
        writer.writerow({
            "nome": p.nome,
            "cargo": p.cargo,
            "setor": p.setor,
            "hora": p.entrada.strftime("%d-%m-%Y %H:%M:%S"),
            "reuniao": reuniao.descricao
        })
    return output.getvalue()

def gerar_qrcode_base64(url):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_b64}"

def enviar_email_com_relatorio(reuniao):
    """Tenta enviar o relatório por e-mail e retorna o status."""
    csv_content = _gerar_csv_content(reuniao)

    email_host = os.environ.get('EMAIL_HOST')
    email_port = int(os.environ.get('EMAIL_PORT', 587))
    email_user = os.environ.get('EMAIL_USER')
    email_pass = os.environ.get('EMAIL_PASS')
    email_to = os.environ.get('RECIPIENT_EMAIL')

    if not all([email_host, email_port, email_user, email_pass, email_to]):
        return {"status": "erro", "mensagem": "Variáveis de ambiente do e-mail não configuradas."}

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_to
    msg['Subject'] = f"Relatório de Presença - {reuniao.descricao}"
    body = f"Olá,\n\nSegue em anexo o relatório de presença para a reunião '{reuniao.descricao}'.\n\nTotal de participantes: {len(reuniao.participantes)}\n"
    msg.attach(MIMEText(body, 'plain'))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(csv_content.encode('utf-8'))
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="relatorio_{reuniao.id}.csv"')
    msg.attach(part)

    server = None
    try:
        server = smtplib.SMTP(email_host, email_port, timeout=15)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, email_to, msg.as_string())
        return {"status": "sucesso", "mensagem": f"Relatório da reunião '{reuniao.descricao}' enviado com sucesso!"}
    except Exception as e:
        app.logger.error(f"Falha ao enviar e-mail: {e}")
        return {"status": "erro", "mensagem": f"O envio do e-mail falhou, mas você ainda pode baixar o relatório. (Erro: {type(e).__name__})"}
    finally:
        if server:
            server.quit()

# --- Rotas da Aplicação ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        descricao = request.form.get("descricao", "Reunião sem descrição").strip()
        if not descricao: flash("A descrição da reunião não pode estar vazia.", "warning"); return redirect(url_for('index'))
        nova_reuniao = Reuniao(descricao=descricao)
        db.session.add(nova_reuniao)
        db.session.commit()
        qrcode_b64 = gerar_qrcode_base64(url_for('checkin', meeting_id=nova_reuniao.id, _external=True))
        return render_template("admin.html", meeting_id=nova_reuniao.id, descricao=descricao, qrcode=qrcode_b64)
    reunioes = Reuniao.query.order_by(Reuniao.data_criacao.desc()).all()
    return render_template("index.html", reunioes=reunioes)

@app.route("/checkin/<meeting_id>", methods=["GET", "POST"])
def checkin(meeting_id):
    reuniao_info = db.get_or_404(Reuniao, meeting_id)
    if reuniao_info.finalizada:
        flash("Esta reunião já foi encerrada e não aceita mais check-ins.", "warning")
        return render_template("checkin_encerrado.html", descricao=reuniao_info.descricao)
    if request.method == "POST":
        nome = request.form.get("nome", "N/A").strip()
        if not nome or nome == "N/A": flash("O campo 'Nome' é obrigatório.", "danger"); return redirect(url_for('checkin', meeting_id=meeting_id))
        nova_presenca = Presenca(
            nome=nome,
            cargo=request.form.get("cargo", "N/A").strip(),
            setor=request.form.get("setor", "N/A").strip(),
            meeting_id=meeting_id
        )
        db.session.add(nova_presenca)
        db.session.commit()
        return render_template("success.html", nome=nome, descricao=reuniao_info.descricao)
    return render_template("checkin.html", meeting_id=meeting_id, descricao=reuniao_info.descricao)

@app.route("/finalizar/<meeting_id>", methods=["POST"])
def finalizar_reuniao(meeting_id):
    reuniao = db.get_or_404(Reuniao, meeting_id)
    
    if not reuniao.finalizada:
        reuniao.finalizada = True
        db.session.commit()
    
    resultado_email = enviar_email_com_relatorio(reuniao)
    
    if resultado_email["status"] == "sucesso":
        flash(resultado_email["mensagem"], "success")
    else:
        flash(resultado_email["mensagem"], "warning")
        # Se o envio do e-mail falhar, o usuário ainda pode baixar o relatório.
        return redirect(url_for('download', meeting_id=meeting_id))

    return render_template("finish.html", reuniao=reuniao)

@app.route("/download/<meeting_id>")
def download(meeting_id):
    reuniao_info = db.get_or_404(Reuniao, meeting_id)
    csv_content = _gerar_csv_content(reuniao_info)
    filename = f"presencas_reuniao_{meeting_id}.csv"

    return send_file(
        io.BytesIO(csv_content.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route("/drop", methods=["GET"])
def drop_tables():
    try:
        with app.app_context():
            db.drop_all()
            db.create_all()
        return jsonify({"status": "sucesso", "mensagem": "Tabelas removidas e recriadas com sucesso!"}), 200
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

