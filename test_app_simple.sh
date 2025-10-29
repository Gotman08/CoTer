#!/bin/bash
# Test simple de l'application Terminal IA sous WSL

cd /mnt/c/Users/nicol/Documents/Projet/TerminalIA
source venv/bin/activate

echo "======================================================================"
echo "TEST 1: Application avec modèle configuré existant (tinyllama)"
echo "======================================================================"
echo ""

# Test avec modèle existant - timeout après 10s
echo "/quit" | timeout 10 python main.py --model tinyllama:latest 2>&1 | head -80

echo ""
echo "======================================================================"
echo "TEST 2: Application avec modèle inexistant (devrait afficher warning)"
echo "======================================================================"
echo ""

# Test avec modèle inexistant - timeout après 10s
echo -e "\\n/quit" | timeout 10 python main.py --model modele-qui-nexiste-pas 2>&1 | head -80

echo ""
echo "======================================================================"
echo "TEST 3: Vérification des modèles disponibles"
echo "======================================================================"
echo ""

curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'Modèles installés: {len(data[\"models\"])}'); [print(f'  • {m[\"name\"]} ({m[\"size\"]/(1024**3):.1f} GB)') for m in data['models']]"

echo ""
echo "======================================================================"
echo "FIN DES TESTS"
echo "======================================================================"
