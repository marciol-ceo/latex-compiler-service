from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import uuid

app = Flask(__name__)
CORS(app)  # Pour permettre les requêtes depuis Firebase Functions

# Configuration
MAX_COMPILE_TIME = 30  # secondes
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@app.route('/', methods=['GET'])
def index():
    """Page d'accueil du service"""
    return jsonify({
        'service': 'MAXA LaTeX Compiler',
        'status': 'running',
        'endpoints': {
            '/health': 'GET - Health check',
            '/compile': 'POST - Compile LaTeX to PDF'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Vérifier que le service est en ligne"""
    return jsonify({
        'status': 'healthy',
        'latex_available': check_latex_installation()
    })

def check_latex_installation():
    """Vérifie que pdflatex est installé"""
    try:
        result = subprocess.run(
            ['pdflatex', '--version'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

@app.route('/compile', methods=['POST'])
def compile_latex():
    """
    Compile du code LaTeX en PDF

    Body JSON:
    {
        "latex_content": "\\documentclass{article}...",
        "filename": "exam.pdf"  # optionnel
    }
    """
    try:
        print(f"📥 [RENDER] Requête reçue sur /compile")
        print(f"🔍 [RENDER] Method: {request.method}")
        print(f"🔍 [RENDER] Headers: {dict(request.headers)}")
        print(f"🔍 [RENDER] Content-Type: {request.content_type}")

        # Validation de la requête
        data = request.get_json()
        print(f"📦 [RENDER] Data reçue: {data is not None}")

        if not data or 'latex_content' not in data:
            print(f"❌ [RENDER] Données invalides: data={data}")
            return jsonify({
                'success': False,
                'error': 'latex_content est requis'
            }), 400

        latex_content = data['latex_content']
        filename = data.get('filename', 'document.pdf')

        print(f"📄 [RENDER] Filename: {filename}")
        print(f"📏 [RENDER] LaTeX content size: {len(latex_content)} chars")

        # Validation de la taille
        if len(latex_content.encode('utf-8')) > MAX_FILE_SIZE:
            print(f"❌ [RENDER] Fichier trop volumineux")
            return jsonify({
                'success': False,
                'error': f'Le fichier LaTeX dépasse {MAX_FILE_SIZE / 1024 / 1024} MB'
            }), 400

        # Créer un dossier temporaire unique
        work_dir = tempfile.mkdtemp(prefix='latex_compile_')
        print(f"📁 [RENDER] Work dir créé: {work_dir}")

        try:
            # Sauvegarder le fichier .tex
            tex_file = os.path.join(work_dir, 'document.tex')
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)

            # Compiler avec pdflatex (2 passes pour les références croisées)
            print(f"🔨 [RENDER] Début compilation pdflatex...")
            pdf_file = compile_latex_to_pdf(work_dir, tex_file)

            if pdf_file and os.path.exists(pdf_file):
                pdf_size = os.path.getsize(pdf_file)
                print(f"✅ [RENDER] PDF généré avec succès: {pdf_size} bytes")
                # Renvoyer le PDF
                return send_file(
                    pdf_file,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=filename
                )
            else:
                # Récupérer les logs d'erreur
                print(f"❌ [RENDER] Compilation échouée, PDF non généré")
                log_file = os.path.join(work_dir, 'document.log')
                error_log = ''
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        error_log = f.read()[-2000:]  # Derniers 2000 caractères
                    print(f"📋 [RENDER] Log LaTeX: {error_log[:500]}...")

                return jsonify({
                    'success': False,
                    'error': 'Erreur de compilation LaTeX',
                    'log': error_log
                }), 500

        finally:
            # Nettoyer le dossier temporaire
            print(f"🧹 [RENDER] Nettoyage du dossier temporaire")
            shutil.rmtree(work_dir, ignore_errors=True)

    except Exception as e:
        print(f"💥 [RENDER] Exception non gérée: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }), 500

def compile_latex_to_pdf(work_dir, tex_file):
    """
    Compile un fichier .tex en PDF avec pdflatex

    Returns:
        str: Chemin du fichier PDF généré ou None en cas d'erreur
    """
    try:
        # Première passe
        result1 = subprocess.run(
            [
                'pdflatex',
                '-interaction=nonstopmode',
                '-halt-on-error',
                '-output-directory', work_dir,
                tex_file
            ],
            cwd=work_dir,
            capture_output=True,
            timeout=MAX_COMPILE_TIME,
            text=True
        )

        # Deuxième passe pour les références croisées
        result2 = subprocess.run(
            [
                'pdflatex',
                '-interaction=nonstopmode',
                '-halt-on-error',
                '-output-directory', work_dir,
                tex_file
            ],
            cwd=work_dir,
            capture_output=True,
            timeout=MAX_COMPILE_TIME,
            text=True
        )

        # Vérifier que le PDF a été créé
        pdf_file = os.path.join(work_dir, 'document.pdf')
        if os.path.exists(pdf_file):
            return pdf_file

        return None

    except subprocess.TimeoutExpired:
        print(f"Compilation timeout après {MAX_COMPILE_TIME}s")
        return None
    except Exception as e:
        print(f"Erreur compilation: {e}")
        return None

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
