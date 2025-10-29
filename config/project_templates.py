"""Templates de projets prédéfinis pour génération rapide"""

# Template pour une application Flask basique
FLASK_BASIC = {
    'name': 'Flask Web App',
    'description': 'Application web Flask basique avec routes et templates',
    'structure': [
        'app',
        'app/templates',
        'app/static',
        'app/static/css',
        'app/static/js'
    ],
    'files': {
        'app/__init__.py': 'Module d\'initialisation Flask',
        'app/routes.py': 'Définition des routes',
        'app/models.py': 'Modèles de données',
        'app/templates/base.html': 'Template HTML de base',
        'app/templates/index.html': 'Page d\'accueil',
        'run.py': 'Script de démarrage',
        'config.py': 'Configuration de l\'application',
        'requirements.txt': 'Dépendances'
    },
    'dependencies': ['Flask', 'python-dotenv'],
    'git_init': True
}

# Template pour une API FastAPI
FASTAPI_REST = {
    'name': 'FastAPI REST API',
    'description': 'API REST avec FastAPI et documentation automatique',
    'structure': [
        'app',
        'app/routers',
        'app/models',
        'app/schemas',
        'tests'
    ],
    'files': {
        'app/__init__.py': 'Package principal',
        'app/main.py': 'Point d\'entrée FastAPI',
        'app/routers/__init__.py': 'Package routers',
        'app/routers/items.py': 'Routes pour items',
        'app/models/__init__.py': 'Package models',
        'app/models/item.py': 'Modèle Item',
        'app/schemas/__init__.py': 'Package schemas',
        'app/schemas/item.py': 'Schéma Pydantic Item',
        'requirements.txt': 'Dépendances',
        '.env.example': 'Variables d\'environnement exemple'
    },
    'dependencies': ['fastapi', 'uvicorn[standard]', 'pydantic', 'python-dotenv'],
    'git_init': True
}

# Template pour une application CLI
CLI_TOOL = {
    'name': 'CLI Tool',
    'description': 'Outil en ligne de commande Python',
    'structure': [
        'src',
        'tests'
    ],
    'files': {
        'src/__init__.py': 'Package principal',
        'src/cli.py': 'Interface CLI',
        'src/core.py': 'Logique métier',
        'main.py': 'Point d\'entrée',
        'requirements.txt': 'Dépendances',
        'README.md': 'Documentation'
    },
    'dependencies': ['click', 'rich'],
    'git_init': True
}

# Template pour analyse de données
DATA_ANALYSIS = {
    'name': 'Data Analysis Project',
    'description': 'Projet d\'analyse de données avec Pandas et Matplotlib',
    'structure': [
        'data',
        'notebooks',
        'src',
        'output'
    ],
    'files': {
        'src/__init__.py': 'Package principal',
        'src/data_loader.py': 'Chargement des données',
        'src/analyzer.py': 'Analyse des données',
        'src/visualizer.py': 'Visualisations',
        'main.py': 'Script principal',
        'requirements.txt': 'Dépendances',
        'README.md': 'Documentation'
    },
    'dependencies': ['pandas', 'numpy', 'matplotlib', 'seaborn', 'jupyter'],
    'git_init': True
}

# Template pour bot Discord
DISCORD_BOT = {
    'name': 'Discord Bot',
    'description': 'Bot Discord avec discord.py',
    'structure': [
        'cogs',
        'utils'
    ],
    'files': {
        'bot.py': 'Point d\'entrée du bot',
        'cogs/__init__.py': 'Package cogs',
        'cogs/general.py': 'Commandes générales',
        'utils/__init__.py': 'Package utils',
        'utils/helpers.py': 'Fonctions utilitaires',
        'config.py': 'Configuration',
        '.env.example': 'Variables d\'environnement exemple',
        'requirements.txt': 'Dépendances',
        'README.md': 'Documentation'
    },
    'dependencies': ['discord.py', 'python-dotenv'],
    'git_init': True
}

# Template pour web scraper
WEB_SCRAPER = {
    'name': 'Web Scraper',
    'description': 'Web scraper avec BeautifulSoup et Requests',
    'structure': [
        'scrapers',
        'data',
        'output'
    ],
    'files': {
        'scrapers/__init__.py': 'Package scrapers',
        'scrapers/base_scraper.py': 'Scraper de base',
        'scrapers/example_scraper.py': 'Exemple de scraper',
        'main.py': 'Script principal',
        'utils.py': 'Fonctions utilitaires',
        'requirements.txt': 'Dépendances',
        'README.md': 'Documentation'
    },
    'dependencies': ['beautifulsoup4', 'requests', 'lxml', 'pandas'],
    'git_init': True
}

# Template pour API REST avec authentification JWT
FASTAPI_JWT = {
    'name': 'FastAPI with JWT Auth',
    'description': 'API FastAPI avec authentification JWT complète',
    'structure': [
        'app',
        'app/routers',
        'app/models',
        'app/schemas',
        'app/core',
        'tests'
    ],
    'files': {
        'app/__init__.py': 'Package principal',
        'app/main.py': 'Point d\'entrée FastAPI',
        'app/core/__init__.py': 'Package core',
        'app/core/security.py': 'Sécurité et JWT',
        'app/core/config.py': 'Configuration',
        'app/routers/__init__.py': 'Package routers',
        'app/routers/auth.py': 'Routes d\'authentification',
        'app/routers/users.py': 'Routes utilisateurs',
        'app/models/__init__.py': 'Package models',
        'app/models/user.py': 'Modèle User',
        'app/schemas/__init__.py': 'Package schemas',
        'app/schemas/user.py': 'Schéma User',
        'app/schemas/token.py': 'Schéma Token',
        'requirements.txt': 'Dépendances',
        '.env.example': 'Variables d\'environnement exemple'
    },
    'dependencies': [
        'fastapi',
        'uvicorn[standard]',
        'pydantic',
        'python-jose[cryptography]',
        'passlib[bcrypt]',
        'python-multipart',
        'python-dotenv'
    ],
    'git_init': True
}

# Dictionnaire de tous les templates
TEMPLATES = {
    'flask_basic': FLASK_BASIC,
    'flask_web': FLASK_BASIC,
    'fastapi_rest': FASTAPI_REST,
    'fastapi_api': FASTAPI_REST,
    'fastapi_jwt': FASTAPI_JWT,
    'cli_tool': CLI_TOOL,
    'cli': CLI_TOOL,
    'data_analysis': DATA_ANALYSIS,
    'data': DATA_ANALYSIS,
    'discord_bot': DISCORD_BOT,
    'discord': DISCORD_BOT,
    'web_scraper': WEB_SCRAPER,
    'scraper': WEB_SCRAPER
}

def get_template(template_name: str):
    """
    Récupère un template par son nom

    Args:
        template_name: Nom du template

    Returns:
        Dict du template ou None
    """
    return TEMPLATES.get(template_name.lower())

def list_templates():
    """
    Liste tous les templates disponibles

    Returns:
        Dict {nom: description}
    """
    return {
        name: template['description']
        for name, template in TEMPLATES.items()
        if not any(name.endswith(suffix) for suffix in ['_web', '_api', '_tool'])  # Éviter les doublons
    }

def get_template_names():
    """
    Retourne la liste des noms de templates

    Returns:
        Liste des noms
    """
    seen = set()
    result = []
    for name, template in TEMPLATES.items():
        if template['name'] not in seen:
            seen.add(template['name'])
            result.append(name)
    return result
