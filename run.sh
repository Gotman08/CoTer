#!/bin/bash
# Script de démarrage pour Terminal IA Autonome

# Couleurs pour l'affichage
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Terminal IA Autonome - Démarrage   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 n'est pas installé${NC}"
    exit 1
fi

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Environnement virtuel non trouvé${NC}"
    echo -e "${GREEN}📦 Création de l'environnement virtuel...${NC}"
    python3 -m venv venv
fi

# Activer l'environnement virtuel
echo -e "${GREEN}🔄 Activation de l'environnement virtuel...${NC}"
source venv/bin/activate

# Vérifier si les dépendances sont installées
if [ ! -f "venv/lib/python*/site-packages/requests/__init__.py" ]; then
    echo -e "${GREEN}📦 Installation des dépendances...${NC}"
    pip install -r requirements.txt
fi

# Vérifier si Ollama est en cours d'exécution
if ! pgrep -x "ollama" > /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama ne semble pas être en cours d'exécution${NC}"
    echo -e "${YELLOW}   Assurez-vous de lancer 'ollama serve' dans un autre terminal${NC}"
    echo ""
fi

# Créer le dossier logs s'il n'existe pas
mkdir -p logs

# Lancer l'application
echo -e "${GREEN}🚀 Lancement du Terminal IA...${NC}"
echo ""
python3 main.py "$@"
