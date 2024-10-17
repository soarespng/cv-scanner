import os
import re
import io
import logging
import mimetypes
from dotenv import load_dotenv
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from pdfminer.high_level import extract_text
from flask import Flask, render_template, request, redirect

load_dotenv()

logging.basicConfig(level=logging.INFO)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)

def extract_text_from_pdf(file):
    file.seek(0)
    return extract_text(io.BytesIO(file.read()))

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def extract_profile_info(text):
    profile_info = {
        'primeiro_nome': 'N/A',
        'segundo_nome': 'N/A',
        'ultimo_nome': 'N/A',
        'telefone': 'N/A',
        'email': 'N/A',
    }
    
    patterns = {
        'nome': r'(?i)nome:\s*([A-Za-zÀ-ÿ\s\.\-]+)',
        'telefone': r'(?i)(telefone|celular|contato):\s*[\(\d{2}\)]*\s*\d{4,5}[-\s]?\d{4}',
        'email': r'(?i)e[-]?mail:\s*([\w\.-]+@[\w\.-]+)|([\w\.-]+@[\w\.-]+)'
    }

    nome_match = re.search(patterns['nome'], text)
    if nome_match:
        nome_completo = clean_text(nome_match.group(1)).strip()
        partes_nome = nome_completo.split()
        if partes_nome:
            profile_info['primeiro_nome'] = partes_nome[0]
            if len(partes_nome) > 2:
                profile_info['segundo_nome'] = partes_nome[1]
                profile_info['ultimo_nome'] = " ".join(partes_nome[2:])
            elif len(partes_nome) == 2:
                profile_info['ultimo_nome'] = partes_nome[1]

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            profile_info[key] = clean_text(match.group(0)).replace(key + ": ", "").strip()

    return profile_info

def check_keywords_in_text(text, keywords):
    text_lower = text.lower()
    keywords_lower = [keyword.lower().strip() for keyword in keywords]
    found_keywords = [keyword for keyword in keywords_lower if keyword in text_lower]
    not_found_keywords = [keyword for keyword in keywords_lower if keyword not in text_lower]
    compatibility = (len(found_keywords) / len(keywords_lower)) * 100 if keywords_lower else 0
    return found_keywords, not_found_keywords, compatibility

def upload_file_to_supabase(file):
    filename = secure_filename(file.filename)
    
    if not filename.endswith('.pdf'):
        raise ValueError("O arquivo deve ter a extensão .pdf")

    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type != 'application/pdf':
        raise ValueError(f"Tipo MIME não suportado: {mime_type}")

    file.seek(0)
    response = supabase.storage.from_('uploads').upload(f"uploads/{filename}", file.read(), {
        'Content-Type': 'application/pdf'
    })

    if response.status_code == 200:
        return supabase.storage.from_('uploads').get_public_url(f"uploads/{filename}")
    else:
        raise Exception("Erro ao fazer upload do arquivo.")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('files')
        keywords = request.form['keywords'].split(',')
        profiles = []

        for file in files:
            try:
                pdf_url = upload_file_to_supabase(file)
                text = extract_text_from_pdf(file)
                profile_info = extract_profile_info(text)
                found_keywords, not_found_keywords, compatibility = check_keywords_in_text(text, keywords)

                profile_info.update({
                    'found_keywords': found_keywords,
                    'not_found_keywords': not_found_keywords,
                    'compatibilidade': f"{compatibility:.2f}%",
                    'filename': pdf_url
                })

                profiles.append(profile_info)

            except Exception as e:
                logging.error(f"Erro ao salvar o arquivo: {str(e)}")
                return f"Erro ao salvar o arquivo: {str(e)}", 500
        
        return render_template('result.html', profiles=profiles)

    return render_template('upload.html')

@app.route('/view/<filename>')
def view_resume(filename):
    return redirect(filename)

if __name__ == '__main__':
    app.run(debug=True)
