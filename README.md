# 📄 MAXA LaTeX Compiler Service

Service de compilation LaTeX en PDF pour l'application MAXA. Ce service tourne sur Render (plan gratuit) et est appelé par Firebase Cloud Functions.

## 🚀 Architecture

```
App Flutter → Firebase Cloud Function → Service Python (Render) → PDF compilé
```

## 📦 Fonctionnalités

- ✅ Compilation LaTeX vers PDF
- ✅ Support de TeX Live complet
- ✅ Packages français (babel, etc.)
- ✅ Packages mathématiques et scientifiques
- ✅ Timeout de sécurité (30s)
- ✅ Validation de taille (10 MB max)
- ✅ Nettoyage automatique des fichiers temporaires

## 🛠️ Installation locale (développement)

### Prérequis

- Python 3.8+
- TeX Live ou MiKTeX

### Installation

```bash
# Installer les dépendances Python
pip install -r requirements.txt

# Lancer le serveur
python app.py
```

Le service sera accessible sur `http://localhost:5000`

## 🌐 Déploiement sur Render

### 1. Créer un compte Render

Rendez-vous sur [render.com](https://render.com) et créez un compte gratuit.

### 2. Connecter votre repo GitHub

1. Poussez ce code sur GitHub
2. Sur Render, cliquez sur "New +" → "Web Service"
3. Connectez votre repo GitHub
4. Render détectera automatiquement le `Dockerfile`

### 3. Configuration

- **Name**: `maxa-latex-compiler`
- **Environment**: Docker
- **Plan**: Free
- **Branch**: main

Render déploiera automatiquement le service !

### 4. Récupérer l'URL

Une fois déployé, copiez l'URL du service (ex: `https://maxa-latex-compiler.onrender.com`)

## 📡 API Endpoints

### GET `/health`

Vérifier l'état du service

**Response:**
```json
{
  "status": "healthy",
  "latex_available": true
}
```

### POST `/compile`

Compiler du code LaTeX en PDF

**Request Body:**
```json
{
  "latex_content": "\\documentclass{article}\\begin{document}Hello\\end{document}",
  "filename": "exam.pdf"
}
```

**Response:**
- **Success**: Fichier PDF (application/pdf)
- **Error**: JSON avec détails

```json
{
  "success": false,
  "error": "Erreur de compilation LaTeX",
  "log": "... logs d'erreur ..."
}
```

## 🔥 Intégration Firebase

Une fois le service déployé, configurez Firebase:

```bash
cd functions
firebase functions:config:set latex.service_url="https://maxa-latex-compiler.onrender.com"
firebase deploy --only functions:compileLaTeXToPdf
```

## 📝 Utilisation côté Flutter

```dart
Future<Uint8List?> compileLaTeXToPdf(String latexContent, String filename) async {
  try {
    final functions = FirebaseFunctions.instanceFor(region: 'us-central1');
    final callable = functions.httpsCallable('compileLaTeXToPdf');

    final result = await callable.call({
      'latexContent': latexContent,
      'filename': filename,
    });

    if (result.data['success'] == true) {
      final pdfBase64 = result.data['pdf'] as String;
      return base64Decode(pdfBase64);
    }

    return null;
  } catch (e) {
    debugPrint('Erreur compilation PDF: $e');
    return null;
  }
}
```

## ⚙️ Configuration avancée

### Variables d'environnement

- `PORT`: Port du serveur (défaut: 5000)

### Limites

- **Timeout**: 30 secondes par compilation
- **Taille max**: 10 MB de code LaTeX
- **Workers**: 2 workers Gunicorn

### Packages LaTeX inclus

- `texlive-latex-base`: Classes et packages de base
- `texlive-latex-extra`: Packages additionnels
- `texlive-fonts-recommended`: Polices recommandées
- `texlive-fonts-extra`: Polices supplémentaires
- `texlive-lang-french`: Support français
- `texlive-science`: Packages scientifiques (amsmath, etc.)
- `texlive-xetex`: XeTeX pour Unicode

## 🔒 Sécurité

- ✅ Timeout pour éviter les compilations infinies
- ✅ Validation de la taille des fichiers
- ✅ Isolation via Docker
- ✅ Nettoyage automatique des fichiers temporaires
- ✅ Pas d'exécution de commandes shell arbitraires

## 📊 Monitoring

### Render Dashboard

Render fournit automatiquement:
- Logs en temps réel
- Métriques CPU/RAM
- Nombre de requêtes
- Temps de réponse

### Health Check

Le endpoint `/health` permet de vérifier que:
- Le service est en ligne
- pdflatex est disponible

## 💰 Coûts

**Plan Render Free:**
- ✅ 750 heures/mois gratuites
- ✅ Sleep après inactivité (redémarre automatiquement)
- ✅ 512 MB RAM
- ✅ Certificat SSL gratuit

**Suffisant pour MAXA car:**
- Compilation rapide (< 5s en général)
- Peu de compilations simultanées
- Service se réveille automatiquement

## 🐛 Troubleshooting

### Le service ne démarre pas

Vérifiez les logs sur Render Dashboard pour voir l'erreur.

### Compilation timeout

Le code LaTeX est trop complexe ou contient une boucle infinie. Vérifiez le code.

### Erreur de packages LaTeX

Vérifiez que le package nécessaire est installé dans le Dockerfile.

### Service en "sleep"

Normal avec le plan free. Le premier appel réveille le service (~ 30-50s), puis il reste actif.

## 📞 Support

Pour toute question, contactez l'équipe MAXA.

## 📄 Licence

© 2024 MAXA. Tous droits réservés.
