import qrcode
from datetime import date

def gerar_qrcode(url):
    # Gerar QR Code
    qr = qrcode.make(url)

    # Salvar como imagem
    data_hoje = date.today().strftime("%d-%m-%Y")
    qr.save(f"reuniao_{data_hoje}.png")
    return f"reuniao_{data_hoje}.png"
