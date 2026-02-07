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
        # Validation de la requête
        data = request.get_json()
        if not data or 'latex_content' not in data:
            return jsonify({
                'success': False,
                'error': 'latex_content est requis'
            }), 400

        latex_content = data['latex_content']
        filename = data.get('filename', 'document.pdf')

        # Validation de la taille
        if len(latex_content.encode('utf-8')) > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': f'Le fichier LaTeX dépasse {MAX_FILE_SIZE / 1024 / 1024} MB'
            }), 400

        # Créer un dossier temporaire unique
        work_dir = tempfile.mkdtemp(prefix='latex_compile_')

        try:
            # Sauvegarder le fichier .tex
            tex_file = os.path.join(work_dir, 'document.tex')
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)

            # Compiler avec pdflatex (2 passes pour les références croisées)
            pdf_file = compile_latex_to_pdf(work_dir, tex_file)

            if pdf_file and os.path.exists(pdf_file):
                # Renvoyer le PDF
                return send_file(
                    pdf_file,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=filename
                )
            else:
                # Récupérer les logs d'erreur
                log_file = os.path.join(work_dir, 'document.log')
                error_log = ''
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        error_log = f.read()[-2000:]  # Derniers 2000 caractères

                return jsonify({
                    'success': False,
                    'error': 'Erreur de compilation LaTeX',
                    'log': error_log
                }), 500

        finally:
            # Nettoyer le dossier temporaire
            shutil.rmtree(work_dir, ignore_errors=True)

    except Exception as e:
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
