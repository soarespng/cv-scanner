from flask import Flask, render_template, request, send_file, abort
from pdfminer.high_level import extract_text
import os
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extract_text_from_pdf(pdf_path):
    text = extract_text(pdf_path)
    return text

def clean_text(text):
    """Limpa o texto extraído."""
    return re.sub(r'\s+', ' ', text).strip()

def extract_profile_info(text):
    profile_info = {
        'primeiro_nome': 'N/A',
        'segundo_nome': 'N/A',
        'ultimo_nome': 'N/A',
        'telefone': 'N/A',
        'email': 'N/A',
    }

    nome_match = re.search(r'(?i)nome:\s*([A-Za-zÀ-ÿ\s\.\-]+)', text)
    if nome_match:
        nome_completo = clean_text(nome_match.group(1)).strip()
        partes_nome = nome_completo.split()

        if len(partes_nome) > 0:
            profile_info['primeiro_nome'] = partes_nome[0]
        
        if len(partes_nome) > 2:
            profile_info['segundo_nome'] = partes_nome[1]
            profile_info['ultimo_nome'] = " ".join(partes_nome[2:])
        elif len(partes_nome) == 2:
            profile_info['ultimo_nome'] = partes_nome[1]

    telefone_match = re.search(r'(?i)(telefone|celular|contato):\s*[\(\d{2}\)]*\s*\d{4,5}[-\s]?\d{4}', text)
    if telefone_match:
        profile_info['telefone'] = clean_text(telefone_match.group(0)).replace("Telefone: ", "").strip()

    email_match = re.search(r'(?i)e[-]?mail:\s*([\w\.-]+@[\w\.-]+)', text)
    if email_match:
        profile_info['email'] = clean_text(email_match.group(1))
    else:
        email_flexible = re.search(r'([\w\.-]+@[\w\.-]+)', text)
        if email_flexible:
            profile_info['email'] = clean_text(email_flexible.group(1))

    return profile_info

def check_keywords_in_text(text, keywords):
    text = text.lower()
    keywords = [keyword.lower().strip() for keyword in keywords]
    keyword_matches = {keyword: keyword in text for keyword in keywords}
    
    total_keywords = len(keywords)
    found_keywords = [keyword for keyword, found in keyword_matches.items() if found]
    not_found_keywords = [keyword for keyword, found in keyword_matches.items() if not found]
    compatibility = (len(found_keywords) / total_keywords) * 100 if total_keywords > 0 else 0
    
    return found_keywords, not_found_keywords, compatibility

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        files = request.files.getlist('files')
        keywords = request.form['keywords'].split(',')
        profiles = []

        for file in files:
            filename = secure_filename(file.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(pdf_path)
            except Exception as e:
                return f"Erro ao salvar o arquivo: {str(e)}", 500

            try:
                text = extract_text_from_pdf(pdf_path)
            except FileNotFoundError:
                return f"Erro: O arquivo {filename} não foi encontrado após o upload.", 404
            except Exception as e:
                return f"Erro ao processar o arquivo {filename}: {str(e)}", 500

            profile_info = extract_profile_info(text)
            found_keywords, not_found_keywords, compatibility = check_keywords_in_text(text, keywords)

            profile_info['found_keywords'] = found_keywords
            profile_info['not_found_keywords'] = not_found_keywords
            profile_info['compatibilidade'] = f"{compatibility:.2f}%"
            profile_info['filename'] = filename

            profiles.append(profile_info)

        return render_template('result.html', profiles=profiles)

    return render_template('upload.html')

@app.route('/view/<filename>')
def view_resume(filename):
    filename = secure_filename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        abort(404, description=f"Erro: O arquivo {filename} não foi encontrado.")

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
