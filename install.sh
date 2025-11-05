#!/usr/bin/env bash

# ╔════════════════════════════════════════════════════════════╗
# ║  CoTer - Script d'Installation                             ║
# ║  Terminal IA Autonome - Shell Hybride Linux                ║
# ╚════════════════════════════════════════════════════════════╝

set -e  # Arrêter en cas d'erreur

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
INSTALL_DIR="/usr/local/bin"
COTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_MIN_VERSION="3.8"
RASPBERRY_PI=false

# ═══════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════

print_header() {
    echo -e "${BLUE}"
    cat << 'EOF'
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║    CoTer - Terminal IA Autonome                            ║
║    Installation                                            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Vérifier si on est root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "Ce script doit être exécuté en tant que root (sudo)"
        exit 1
    fi
}

# Détecter le système
detect_system() {
    print_info "Détection du système..."

    # Détecter Raspberry Pi
    if [[ -f /proc/device-tree/model ]] && grep -q "Raspberry Pi" /proc/device-tree/model; then
        RASPBERRY_PI=true
        print_success "Raspberry Pi détecté"
    fi

    # Vérifier l'OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_success "OS: Linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_success "OS: macOS"
    else
        print_warning "OS non supporté officiellement: $OSTYPE"
    fi
}

# Vérifier Python
check_python() {
    print_info "Vérification de Python..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 n'est pas installé"
        echo "Installez Python 3.8+ et relancez ce script"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION installé"

    # Vérifier la version minimale
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if (( PYTHON_MAJOR < 3 || (PYTHON_MAJOR == 3 && PYTHON_MINOR < 8) )); then
        print_error "Python 3.8+ est requis (version actuelle: $PYTHON_VERSION)"
        exit 1
    fi
}

# Vérifier Ollama
check_ollama() {
    print_info "Vérification d'Ollama..."

    if ! command -v ollama &> /dev/null; then
        print_warning "Ollama n'est pas installé"
        echo ""
        echo "Installez Ollama depuis: https://ollama.ai"
        echo "Linux: curl https://ollama.ai/install.sh | sh"
        echo ""
        read -p "Continuer sans Ollama? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        OLLAMA_VERSION=$(ollama --version 2>/dev/null || echo "unknown")
        print_success "Ollama installé: $OLLAMA_VERSION"
    fi
}

# Installer les dépendances Python
install_dependencies() {
    print_info "Installation des dépendances Python..."

    cd "$COTER_DIR"

    # Créer un venv si nécessaire
    if [[ ! -d "venv" ]]; then
        print_info "Création de l'environnement virtuel..."
        python3 -m venv venv
        print_success "Environnement virtuel créé"
    fi

    # Activer le venv et installer les dépendances
    source venv/bin/activate

    if [[ -f "requirements.txt" ]]; then
        pip install --upgrade pip > /dev/null 2>&1
        pip install -r requirements.txt > /dev/null 2>&1
        print_success "Dépendances Python installées"
    else
        print_warning "requirements.txt non trouvé"
    fi

    deactivate
}

# Créer le wrapper script
create_wrapper() {
    print_info "Création du script wrapper..."

    cat > "$INSTALL_DIR/coter" << EOF
#!/usr/bin/env bash
# CoTer Shell Wrapper

# Activer le venv et lancer CoTer
cd "$COTER_DIR"
source venv/bin/activate
exec python main.py "\$@"
EOF

    chmod +x "$INSTALL_DIR/coter"
    print_success "Script wrapper créé: $INSTALL_DIR/coter"
}

# Configuration Raspberry Pi
configure_raspberry_pi() {
    if [[ "$RASPBERRY_PI" != true ]]; then
        return
    fi

    print_info "Configuration spécifique Raspberry Pi..."

    # Créer un fichier de config optimisé
    cat > "$COTER_DIR/.env.raspberry" << EOF
# Configuration optimisée Raspberry Pi
CACHE_MAX_SIZE=50
AGENT_MAX_WORKERS=2
LOW_POWER_MODE=true
OPTIMIZE_CPU_USAGE=true
EOF

    # Si .env n'existe pas, le créer basé sur .env.raspberry
    if [[ ! -f "$COTER_DIR/.env" ]]; then
        cp "$COTER_DIR/.env.raspberry" "$COTER_DIR/.env"
        print_success "Fichier .env créé avec optimisations Raspberry Pi"
    else
        print_info "Fichier .env existant conservé"
        print_info "Voir .env.raspberry pour les optimisations recommandées"
    fi
}

# Ajouter à /etc/shells
add_to_shells() {
    print_info "Ajout de CoTer aux shells autorisés..."

    if grep -q "$INSTALL_DIR/coter" /etc/shells; then
        print_info "CoTer déjà dans /etc/shells"
    else
        echo "$INSTALL_DIR/coter" >> /etc/shells
        print_success "CoTer ajouté à /etc/shells"
    fi
}

# Créer des raccourcis
create_shortcuts() {
    print_info "Création des raccourcis..."

    # Créer un alias bash
    cat > /etc/profile.d/coter.sh << 'EOF'
# CoTer Shell Aliases
alias coter='/usr/local/bin/coter'
EOF

    chmod +x /etc/profile.d/coter.sh
    print_success "Alias créé: 'coter'"
}

# Vérifier l'installation
verify_installation() {
    print_info "Vérification de l'installation..."

    if [[ -x "$INSTALL_DIR/coter" ]]; then
        print_success "CoTer installé avec succès"
        return 0
    else
        print_error "L'installation a échoué"
        return 1
    fi
}

# Afficher les instructions post-installation
print_post_install() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Installation terminée avec succès!                        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Pour utiliser CoTer:${NC}"
    echo ""
    echo "  1. Lancer CoTer:"
    echo -e "     ${YELLOW}coter${NC}"
    echo ""
    echo "  2. Définir comme shell par défaut (optionnel):"
    echo -e "     ${YELLOW}chsh -s $INSTALL_DIR/coter${NC}"
    echo ""
    echo "  3. Tester les 3 modes:"
    echo -e "     ${YELLOW}# Mode MANUAL (par défaut)${NC}"
    echo "     > ls -la"
    echo ""
    echo -e "     ${YELLOW}# Mode AUTO${NC}"
    echo "     > /auto"
    echo "     > liste les fichiers"
    echo ""
    echo -e "     ${YELLOW}# Mode AGENT${NC}"
    echo "     > /agent crée un script hello.py"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "  README: $COTER_DIR/README.md"
    echo "  Config: $COTER_DIR/config/shell_config.yaml"
    echo ""

    if [[ "$RASPBERRY_PI" == true ]]; then
        echo -e "${YELLOW}Note Raspberry Pi:${NC}"
        echo "  Configuration optimisée créée dans .env.raspberry"
        echo "  Cache limité à 50 MB"
        echo "  2 workers max pour le multiprocessing"
        echo ""
    fi
}

# ═══════════════════════════════════════════════════════════
# PROGRAMME PRINCIPAL
# ═══════════════════════════════════════════════════════════

main() {
    # Parser les arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --raspberry-pi)
                RASPBERRY_PI=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --raspberry-pi    Configuration optimisée Raspberry Pi"
                echo "  --help, -h        Afficher cette aide"
                exit 0
                ;;
            *)
                echo "Option inconnue: $1"
                echo "Utilisez --help pour l'aide"
                exit 1
                ;;
        esac
    done

    print_header

    # Vérifications
    check_root
    detect_system
    check_python
    check_ollama

    # Installation
    install_dependencies
    create_wrapper
    add_to_shells
    create_shortcuts

    # Configuration Raspberry Pi si nécessaire
    configure_raspberry_pi

    # Vérification finale
    if verify_installation; then
        print_post_install
        exit 0
    else
        print_error "L'installation a échoué"
        exit 1
    fi
}

# Lancer le script
main "$@"
