import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dbSettings.presenca_schema import Presenca
from dbSettings.reuniao_schema import Reuniao
from app import db, app
def gerar_e_enviar_relatorio_por_reuniao(meeting_id):
    reuniao = db.session.get(Reuniao, meeting_id)
    if not reuniao:
        return {"status": "erro", "mensagem": "Reunião não encontrada."}

    # Marca a reunião como finalizada
    reuniao.finalizada = True
    db.session.commit()

    # Gera o conteúdo do CSV em memória
    csv_header = "Nome,Cargo,Setor,Horario_Checkin\n"
    csv_rows = [f"{p.nome},{p.cargo},{p.setor},{p.entrada.strftime('%Y-%m-%d %H:%M:%S')}\n" for p in reuniao.participantes]
    csv_content = csv_header + "".join(csv_rows)

    # Configurações de E-mail a partir das variáveis de ambiente
    email_host = os.environ.get('EMAIL_HOST')
    email_port = int(os.environ.get('EMAIL_PORT', 587))
    email_user = os.environ.get('EMAIL_USER')
    email_pass = os.environ.get('EMAIL_PASS')
    email_to = os.environ.get('EMAIL_TO')

    if not all([email_host, email_port, email_user, email_pass, email_to]):
        return {"status": "erro", "mensagem": "Variáveis de ambiente do e-mail não configuradas."}

    # Cria a mensagem de e-mail
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_to
    msg['Subject'] = f"Relatório de Presença - {reuniao.descricao}"
    body = f"Olá,\n\nSegue em anexo o relatório de presença para a reunião '{reuniao.descricao}'.\n\nTotal de participantes: {len(reuniao.participantes)}\n"
    msg.attach(MIMEText(body, 'plain'))

    # Anexa o arquivo CSV
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(csv_content.encode('utf-8'))
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="relatorio_{meeting_id}.csv"')
    msg.attach(part)

    try:
        # Conecta ao servidor SMTP de forma segura e envia o e-mail
        server = smtplib.SMTP(email_host, email_port)
        server.starttls()  # Inicia a criptografia TLS
        server.login(email_user, email_pass)
        server.sendmail(email_user, email_to, msg.as_string())
        return {"status": "sucesso", "mensagem": f"Relatório da reunião '{reuniao.descricao}' enviado com sucesso!"}
    except Exception as e:
        app.logger.error(f"Falha ao enviar e-mail: {e}") # Loga o erro para depuração
        return {"status": "erro", "mensagem": f"Falha ao conectar com o servidor de e-mail. ({type(e).__name__})"}
    finally:
        if 'server' in locals() and server:
            server.quit()