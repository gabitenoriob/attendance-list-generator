# Gerador de Lista de Presença com QR Code
Disponivel em: [https://attendance-list-generator.onrender.com]
Um sistema simples e eficiente para automatizar o controle de presença através de QR codes. Ideal para reuniões, aulas e eventos.

## Descrição
Este projeto foi criado para modernizar e automatizar o controle de presença. O sistema gera um QR code que, ao ser escaneado pelos participantes, os direciona para um formulário de registro. As informações são salvas em um banco de dados e, ao final do evento, uma lista de presença é exportada em formato CSV.

## Funcionalidades
Geração de QR Code: Cria um QR code único que leva ao formulário de registro.

Formulário Web: Uma interface simples para os participantes inserirem suas informações.

Persistência de Dados: Armazena os registros de presença em um banco de dados PostgreSQL.

Exportação para CSV: Ao final da reunião, o sistema gera um arquivo .csv com a lista de todos os participantes.

## Tecnologias Utilizadas
Backend: Flask, Flask-SQLAlchemy

Banco de Dados: PostgreSQL (via psycopg2-binary)

Geração de QR Code: qrcode com Pillow

Manipulação de Dados: pandas para exportação CSV

Servidor WSGI: Gunicorn (para deploy)

Gerenciamento de Ambiente: python-dotenv

## Pré-requisitos
Python 3.9+

Pip (gerenciador de pacotes)

Um banco de dados PostgreSQL em execução.

##Instalação e Uso
Clone o repositório:

git clone [https://github.com/gabitenoriob/attendance-list-generator.git](https://github.com/gabitenoriob/attendance-list-generator.git)
cd attendance-list-generator

Crie e ative um ambiente virtual (Recomendado)


Instale as dependências:
pip install -r requirements.txt

Configure as Variáveis de Ambiente:
Crie um arquivo chamado .env na raiz do projeto. Ele será usado para armazenar informações sensíveis, como a conexão com o banco de dados.

Exemplo de conteúdo para o arquivo .env:
DATABASE_URL="postgresql://USUARIO:SENHA@HOST:PORTA/NOME_DO_BANCO"

Substitua pelos dados de acesso do seu banco de dados PostgreSQL.

## Execute a aplicação (Desenvolvimento):

python app.py

Gere o QR Code:
Acesse o endereço fornecido no terminal (geralmente http://127.0.0.1:5000) em seu navegador para iniciar a sessão e exibir o QR code.

Registre a presença:
Os participantes devem escanear o QR code com seus dispositivos para acessar o formulário e preencher suas informações.

Exporte o CSV:
Ao final da reunião, utilize a interface da aplicação para encerrar a sessão e baixar o arquivo .csv com a lista de presença.
