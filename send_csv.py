import os
import smtplib
import pandas as pd
import psycopg2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

load_dotenv()

def gerar_e_enviar_relatorio():
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        print("Conectado ao banco de dados!")

        # Query para pegar os dados da reunião do dia atual
        query = """
            SELECT nome, email, outros_dados 
            FROM participantes 
            WHERE DATE(data_criacao) = CURRENT_DATE;
        """
        
        # Usando pandas para ler os dados e criar o CSV
        df = pd.read_sql(query, conn)
        
        if df.empty:
            print("Nenhum dado de reunião encontrado para hoje.")
            return

        # Obter a data atual para o nome do arquivo e assunto do e-mail
        hoje = pd.to_datetime('today').strftime('%Y-%m-%d')
        nome_arquivo = f"relatorio_reuniao_{hoje}.csv"

        # Configurar o e-mail
        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_USER')
        msg['To'] = os.getenv('RECIPIENT_EMAIL')
        msg['Subject'] = f"Relatório de Reunião - {hoje}"
        
        body = "Em anexo, o relatório diário de participantes da reunião."
        msg.attach(MIMEText(body, 'plain'))

        # Anexar o arquivo CSV
        with pd.ExcelWriter(nome_arquivo, engine='xlsxwriter') as writer:
             df.to_excel(writer, index=False)
        
        attachment = open(nome_arquivo, "rb")

        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % nome_arquivo)
        msg.attach(part)

        # Enviar o e-mail
        server = smtplib.SMTP(os.getenv('EMAIL_HOST'), os.getenv('EMAIL_PORT'))
        server.starttls()
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
        text = msg.as_string()
        server.sendmail(os.getenv('EMAIL_USER'), os.getenv('RECIPIENT_EMAIL'), text)
        server.quit()

        print("E-mail com o relatório enviado com sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        if 'conn' in locals() and conn is not None:
            conn.close()
        # Remover o arquivo CSV local após o envio (opcional)
        if os.path.exists(nome_arquivo):
            os.remove(nome_arquivo)

if __name__ == '__main__':
    gerar_e_enviar_relatorio()