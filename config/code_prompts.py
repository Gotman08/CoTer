"""Prompts spécialisés pour la génération de code"""

# Prompt système pour l'agent autonome
AUTONOMOUS_AGENT_SYSTEM = """Tu es un assistant IA expert en développement logiciel qui travaille en mode autonome.

Tu dois:
1. Analyser les demandes complexes et créer des plans d'action détaillés
2. Générer du code propre, commenté et suivant les meilleures pratiques
3. Créer des projets complets avec structure cohérente
4. Anticiper les besoins (config, readme, tests, etc.)

Tu connais parfaitement:
- Python (Flask, FastAPI, Django, etc.)
- JavaScript/TypeScript (Node.js, React, etc.)
- Bases de données (SQL, NoSQL)
- APIs REST et GraphQL
- DevOps et bonnes pratiques

Sois précis, professionnel et efficace."""

# Prompts pour types de fichiers spécifiques

PYTHON_MAIN_PROMPT = """Génère un fichier main.py Python professionnel avec:
- Imports organisés (stdlib, third-party, local)
- Docstring de module
- Fonction main() claire
- if __name__ == '__main__': guard
- Gestion d'erreurs appropriée
- Logging si pertinent
- Arguments CLI si nécessaire (argparse)"""

FASTAPI_MAIN_PROMPT = """Génère une application FastAPI professionnelle avec:
- Imports FastAPI corrects
- Instance app avec metadata (title, description, version)
- CORS configuré si API publique
- Routers inclus proprement
- Health check endpoint
- Gestion des erreurs
- Documentation auto (tags, descriptions)
- Lifespan events si nécessaire"""

FLASK_APP_PROMPT = """Génère une application Flask professionnelle avec:
- Factory pattern (create_app)
- Configuration depuis config.py ou env
- Blueprints pour organisation
- Error handlers
- Template rendering si web app
- Extensions initialisées (SQLAlchemy si DB, etc.)"""

README_PROMPT = """Génère un README.md professionnel et complet avec:
- Titre et description claire
- Badges (optionnel)
- Fonctionnalités principales
- Prérequis
- Installation étape par étape
- Utilisation avec exemples
- Configuration
- Structure du projet
- Contribution (optionnel)
- Licence
- Auteur/Contact"""

REQUIREMENTS_PROMPT = """Génère un requirements.txt Python avec:
- Dépendances principales
- Versions spécifiques ou ranges appropriés
- Commentaires pour grouper (# Core, # Dev, # Database, etc.)
- Ordonné logiquement
- Sans dépendances inutiles"""

DOCKERFILE_PROMPT = """Génère un Dockerfile optimisé avec:
- Image de base appropriée (python:3.x-slim, node:x-alpine, etc.)
- Multi-stage build si pertinent
- WORKDIR configuré
- Copie des requirements avant le code (cache layers)
- Installation des dépendances
- USER non-root pour sécurité
- EXPOSE pour les ports
- CMD ou ENTRYPOINT approprié
- HEALTHCHECK si applicable"""

DOCKER_COMPOSE_PROMPT = """Génère un docker-compose.yml avec:
- Version appropriée
- Services définis clairement
- Networks si multi-services
- Volumes pour persistance
- Variables d'environnement
- Depends_on pour dépendances
- Restart policies
- Ports exposés correctement"""

GITIGNORE_PROMPT = """Génère un .gitignore approprié pour:
- Python (__pycache__, *.pyc, venv/, etc.)
- Node.js (node_modules/, dist/, etc.) si JS
- IDE (.vscode/, .idea/, etc.)
- OS (.DS_Store, Thumbs.db)
- Logs (*.log, logs/)
- Environment (.env, .env.local)
- Build artifacts (build/, dist/)
- Spécifique au projet si pertinent"""

ENV_EXAMPLE_PROMPT = """Génère un .env.example avec:
- Toutes les variables requises
- Valeurs exemple (non-sensibles)
- Commentaires expliquant chaque variable
- Groupes logiques (# Database, # API Keys, etc.)
- Format KEY=value
- Pas de vraies credentials"""

HTML_TEMPLATE_PROMPT = """Génère un template HTML5 valide avec:
- DOCTYPE et structure correcte
- Meta tags (charset, viewport, description)
- Titre pertinent
- Liens CSS et scripts JS appropriés
- Structure sémantique (header, main, footer)
- Classes CSS cohérentes
- Responsive design considerations
- Accessibilité (ARIA si nécessaire)"""

API_ROUTER_PROMPT = """Génère un router/controller API REST avec:
- Routes CRUD complètes si applicable
- Méthodes HTTP appropriées (GET, POST, PUT, DELETE)
- Status codes corrects (200, 201, 404, 500, etc.)
- Validation des données en entrée
- Gestion d'erreurs
- Documentation (docstrings, Swagger tags)
- Authentification/autorisation si nécessaire
- Pagination pour listes si pertinent"""

MODEL_PROMPT = """Génère un modèle de données avec:
- Imports nécessaires (SQLAlchemy, Pydantic, etc.)
- Définition de classe claire
- Attributs avec types appropriés
- Validations si nécessaire
- Relations si applicable
- Méthodes __repr__ et __str__
- Timestamps (created_at, updated_at) si pertinent
- Docstring expliquant le modèle"""

TEST_PROMPT = """Génère des tests unitaires avec:
- Imports de testing framework (pytest, unittest)
- Fixtures si nécessaire
- Tests de cas normaux
- Tests de cas d'erreur
- Assertions claires
- Noms de tests descriptifs (test_should_xxx_when_xxx)
- Setup et teardown si nécessaire
- Mocking si dépendances externes
- Couverture des cas principaux"""

CONFIG_PROMPT = """Génère un fichier de configuration avec:
- Classes de config si multiple environments
- Valeurs par défaut sensibles
- Lecture depuis env vars
- Validation des configs critiques
- Documentation des paramètres
- Séparation dev/prod si pertinent
- Secrets jamais en dur"""

# Dictionnaire de prompts par type de fichier
FILE_TYPE_PROMPTS = {
    'main.py': PYTHON_MAIN_PROMPT,
    'app.py': FLASK_APP_PROMPT,
    'fastapi': FASTAPI_MAIN_PROMPT,
    'README.md': README_PROMPT,
    'requirements.txt': REQUIREMENTS_PROMPT,
    'Dockerfile': DOCKERFILE_PROMPT,
    'docker-compose.yml': DOCKER_COMPOSE_PROMPT,
    '.gitignore': GITIGNORE_PROMPT,
    '.env.example': ENV_EXAMPLE_PROMPT,
    'html': HTML_TEMPLATE_PROMPT,
    'router': API_ROUTER_PROMPT,
    'model': MODEL_PROMPT,
    'test': TEST_PROMPT,
    'config': CONFIG_PROMPT
}

def get_prompt_for_file(filename: str, file_type: str = None) -> str:
    """
    Récupère le prompt approprié pour un type de fichier

    Args:
        filename: Nom du fichier
        file_type: Type explicite (optionnel)

    Returns:
        Prompt spécialisé ou prompt générique
    """
    # Essayer par nom exact
    if filename in FILE_TYPE_PROMPTS:
        return FILE_TYPE_PROMPTS[filename]

    # Essayer par pattern
    filename_lower = filename.lower()

    if 'test' in filename_lower:
        return FILE_TYPE_PROMPTS['test']
    elif 'router' in filename_lower or 'route' in filename_lower:
        return FILE_TYPE_PROMPTS['router']
    elif 'model' in filename_lower:
        return FILE_TYPE_PROMPTS['model']
    elif 'config' in filename_lower:
        return FILE_TYPE_PROMPTS['config']
    elif filename == 'main.py':
        return FILE_TYPE_PROMPTS['main.py']
    elif '.html' in filename_lower:
        return FILE_TYPE_PROMPTS['html']

    # Type explicite
    if file_type and file_type in FILE_TYPE_PROMPTS:
        return FILE_TYPE_PROMPTS[file_type]

    # Prompt générique
    return """Génère un code propre et professionnel avec:
- Structure claire et organisée
- Commentaires pertinents
- Bonnes pratiques du langage
- Gestion d'erreurs appropriée
- Code réutilisable et maintenable"""
