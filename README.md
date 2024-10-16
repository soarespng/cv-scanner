# cv-scanner
# Projeto Flask para Extração de Informações de PDFs

Este projeto é uma aplicação Flask que permite o upload de arquivos PDF e a extração de informações, como nome, telefone e email. Além disso, ele verifica a compatibilidade de palavras-chave fornecidas pelo usuário.

## Funcionalidades

- Upload de múltiplos arquivos PDF.
- Extração de texto de arquivos PDF usando `pdfminer`.
- Identificação de informações de perfil, como nome, telefone e email.
- Verificação de palavras-chave e cálculo de compatibilidade.
- Visualização dos arquivos PDF carregados.

## Tecnologias Utilizadas

- Python
- Flask
- pdfminer.six
- Gunicorn (para deploy)

## Pré-requisitos

- Python 3.x
- Pip

## Instalação

1. Clone o repositório:
    git clone <https://github.com/soarespng/cv-scanner>
    cd <cv-scanner>
2. Instale as dependências:
    pip install -r requirements.txt
3. Para executar a aplicação em modo de desenvolvimento, use:
    python api/app.py
