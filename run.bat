@echo off
REM Script de démarrage pour Terminal IA Autonome (Windows)

echo ╔════════════════════════════════════════╗
echo ║   Terminal IA Autonome - Démarrage   ║
echo ╚════════════════════════════════════════╝
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou n'est pas dans le PATH
    pause
    exit /b 1
)

REM Vérifier si l'environnement virtuel existe
if not exist "venv\" (
    echo ⚠️  Environnement virtuel non trouvé
    echo 📦 Création de l'environnement virtuel...
    python -m venv venv
)

REM Activer l'environnement virtuel
echo 🔄 Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Installer les dépendances si nécessaire
if not exist "venv\Lib\site-packages\requests\" (
    echo 📦 Installation des dépendances...
    pip install -r requirements.txt
)

REM Créer le dossier logs s'il n'existe pas
if not exist "logs\" mkdir logs

REM Lancer l'application
echo 🚀 Lancement du Terminal IA...
echo.
python main.py %*

pause
