"""Constantes centralisées pour le projet"""

from pathlib import Path


# ===== CHEMINS =====
HOME_DIR = Path.home()
APP_DIR = HOME_DIR / ".terminal-ia"
CACHE_DIR = APP_DIR / "cache"
SNAPSHOTS_DIR = APP_DIR / "snapshots"
LOGS_DIR = Path("./logs")


# ===== LIMITES =====
MAX_CACHE_SIZE_MB = 500
MAX_CACHE_TTL_HOURS = 24
MAX_HISTORY_SIZE = 100
MAX_SNAPSHOTS = 10
MAX_COMMAND_OUTPUT_LENGTH = 5000
MAX_AGENT_STEPS = 50
MAX_AGENT_DURATION_MINUTES = 30
MAX_RETRY_ATTEMPTS = 3

# Limites pour le mode AUTO itératif
MAX_AUTO_ITERATIONS = 15  # Limite de sécurité pour éviter les boucles infinies

# Limites de buffer pour sortie commande (protection mémoire)
MAX_OUTPUT_SIZE_BYTES = 1 * 1024 * 1024  # 1MB max pour stdout/stderr
OUTPUT_BUFFER_SIZE = 8192  # 8KB buffer pour lecture streaming


# ===== TIMEOUTS =====
OLLAMA_TIMEOUT_SECONDS = 60
COMMAND_EXECUTION_TIMEOUT = 120000  # milliseconds


# ===== PERFORMANCE =====
DEFAULT_PARALLEL_WORKERS = "auto"
MIN_PARALLEL_WORKERS = 2
MAX_PARALLEL_WORKERS = 8

# ===== MULTIPROCESSING =====
# Type d'exécuteur: 'process' (vrai parallélisme) ou 'thread' (concurrent I/O)
PARALLEL_EXECUTOR_TYPE = 'process'  # 'process' = multiprocessing, 'thread' = threading

# Méthode de démarrage des processus ('spawn', 'fork', 'forkserver')
# 'spawn' est recommandé pour Windows et est le plus sûr
PARALLEL_PROCESS_START_METHOD = 'spawn'

# Seuil minimum de tâches pour activer le multiprocessing
# En dessous de ce seuil, on utilise l'exécution séquentielle (évite l'overhead)
MIN_TASKS_FOR_PARALLEL = 2

# Fallback automatique sur threading si pickling échoue
PARALLEL_FALLBACK_TO_THREAD = True


# ===== AUTO-CORRECTION =====
AUTO_CORRECTION_CONFIDENCE_THRESHOLD = 0.6
MAX_CORRECTION_HISTORY = 50


# ===== AFFICHAGE =====
SECTION_WIDTH = 60
PROGRESS_BAR_LENGTH = 40


# ===== CACHE =====
CACHE_EVICTION_STRATEGIES = ["lru", "lfu", "fifo"]
DEFAULT_CACHE_EVICTION = "lru"


# ===== NIVEAUX DE RISQUE =====
RISK_LEVELS = {
    'LOW': 'low',
    'MEDIUM': 'medium',
    'HIGH': 'high',
    'BLOCKED': 'blocked'
}


# ===== ACTIONS AGENT =====
AGENT_ACTIONS = {
    'CREATE_STRUCTURE': 'create_structure',
    'CREATE_FILE': 'create_file',
    'RUN_COMMAND': 'run_command',
    'GIT_COMMIT': 'git_commit'
}


# ===== ICÔNES D'ACTION =====
ACTION_ICONS = {
    'create_structure': '📁',
    'create_file': '📝',
    'run_command': '⚙️',
    'git_commit': '📤'
}


# ===== TYPES D'ERREUR AUTO-CORRECTION =====
ERROR_TYPES = {
    'COMMAND_NOT_FOUND': 'command_not_found',
    'PERMISSION_DENIED': 'permission_denied',
    'SYNTAX_ERROR': 'syntax_error',
    'MODULE_NOT_FOUND': 'module_not_found',
    'FILE_NOT_FOUND': 'file_not_found',
    'CONNECTION_ERROR': 'connection_error',
    'DEPENDENCY_ERROR': 'dependency_error',
    'PORT_IN_USE': 'port_in_use',
    'UNKNOWN': 'unknown'
}


# ===== COMMANDES SPÉCIALES =====
SPECIAL_COMMANDS = [
    '/help', '/clear', '/history', '/models', '/info', '/templates',
    '/agent', '/pause', '/resume', '/stop', '/quit',
    '/cache', '/hardware', '/rollback', '/security', '/corrections'
]


# ===== MESSAGES D'ERREUR COURANTS =====
ERROR_MESSAGES = {
    'NO_AGENT': "❌ Le mode agent n'est pas activé",
    'NO_CACHE': "⚠️  Le cache n'est pas activé",
    'NO_SNAPSHOTS': "⚠️  Aucun snapshot disponible",
    'NO_ERRORS': "✅ Aucune erreur détectée",
    'UNKNOWN_COMMAND': "❌ Commande inconnue: {}",
    'COMMAND_CANCELLED': "❌ Commande annulée",
    'OPERATION_CANCELLED': "❌ Opération annulée"
}


# ===== CONFIRMATIONS =====
CONFIRMATION_KEYWORDS = {
    'YES': ['oui', 'o', 'yes', 'y'],
    'NO': ['non', 'n', 'no']
}


# ===== CODES DE SORTIE =====
EXIT_CODES = {
    'SUCCESS': 0,
    'GENERAL_ERROR': 1,
    'COMMAND_NOT_FOUND': 127,
    'PERMISSION_DENIED': 126
}
