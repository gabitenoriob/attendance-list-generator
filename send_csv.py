from datetime import datetime
import os
import smtplib
import pandas as pd
import psycopg2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dbSettings.database import db
from dbSettings.reuniao_schema import Reuniao
from dbSettings.presenca_schema import Presenca
load_dotenv()

def gerar_e_enviar_relatorio_por_reuniao(meeting_id):
    """
    Busca os dados de uma reunião específica, gera um CSV e o envia por e-mail.
    """
    try:
        # Busca a reunião e as presenças associadas usando SQLAlchemy
        reuniao = db.get_or_404(Reuniao, meeting_id)
        presencas = db.session.execute(db.select(Presenca).filter_by(meeting_id=meeting_id)).scalars().all()

        if not presencas:
            print(f"Nenhuma presença encontrada para a reunião {meeting_id}.")
            return {"status": "info", "mensagem": "Nenhuma presença para gerar relatório."}

        # Converte os dados para um formato que o Pandas entende (lista de dicionários)
        dados_para_df = []
        for p in presencas:
            dados_para_df.append({
                "nome": p.nome,
                "cargo": p.cargo,
                "setor": p.setor,
                "entrada": p.entrada.strftime("%d-%m-%Y %H:%M:%S"),
                "descricao_reuniao": reuniao.descricao
            })
        
        df = pd.DataFrame(dados_para_df)
        
        # --- Geração do CSV em memória ---
        # Não precisamos mais salvar o arquivo no disco
        csv_output = df.to_csv(index=False, encoding='utf-8')
        
        # Obter a data para o nome do arquivo e assunto do e-mail
        hoje = datetime.now().strftime('%Y-%m-%d')
        nome_arquivo = f"relatorio_{reuniao.descricao.replace(' ', '_')}_{hoje}.csv"

        # --- Configuração e Envio do E-mail ---
        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_USER')
        msg['To'] = os.getenv('RECIPIENT_EMAIL')
        msg['Subject'] = f"Relatório da Reunião: {reuniao.descricao}"
        
        body = f"Em anexo, o relatório de presença para a reunião '{reuniao.descricao}' finalizada em {hoje}."
        msg.attach(MIMEText(body, 'plain'))

        # Anexar o arquivo CSV
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(csv_output.encode('utf-8'))
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename={nome_arquivo}")
        msg.attach(part)

        # Enviar o e-mail
        server = smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT')))
        server.starttls()
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
        text = msg.as_string()
        server.sendmail(os.getenv('EMAIL_USER'), os.getenv('RECIPIENT_EMAIL'), text)
        server.quit()

        print(f"E-mail com o relatório da reunião {meeting_id} enviado com sucesso!")
        return {"status": "sucesso", "mensagem": "Relatório enviado com sucesso!"}

    except Exception as e:
        print(f"Ocorreu um erro ao gerar/enviar relatório para a reunião {meeting_id}: {e}")
        return {"status": "erro", "mensagem": str(e)}
