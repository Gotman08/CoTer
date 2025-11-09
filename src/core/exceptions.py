"""
Exceptions personnalisées pour CoTer
Hiérarchie d'exceptions pour une meilleure gestion des erreurs
"""


class CoTerException(Exception):
    """
    Exception de base pour toutes les erreurs CoTer

    Toutes les exceptions spécifiques au projet héritent de celle-ci
    pour permettre un catch global si nécessaire
    """
    pass


class OllamaConnectionError(CoTerException):
    """
    Erreur de connexion au serveur Ollama

    Levée quand:
    - Le serveur Ollama n'est pas accessible
    - Timeout lors de la connexion
    - URL invalide
    """
    def __init__(self, host: str, message: str = None):
        self.host = host
        self.message = message or f"Impossible de se connecter à Ollama sur {host}"
        super().__init__(self.message)


class OllamaModelNotFoundError(CoTerException):
    """
    Modèle Ollama introuvable

    Levée quand:
    - Le modèle configuré n'existe pas sur le serveur
    - Aucun modèle n'est disponible
    """
    def __init__(self, model: str, message: str = None):
        self.model = model
        self.message = message or f"Modèle Ollama '{model}' introuvable"
        super().__init__(self.message)


class CommandExecutionError(CoTerException):
    """
    Erreur lors de l'exécution d'une commande shell

    Levée quand:
    - La commande échoue (exit code != 0)
    - Timeout
    - Permissions insuffisantes
    """
    def __init__(self, command: str, exit_code: int = None, stderr: str = None):
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        message = f"Échec de la commande: {command}"
        if exit_code is not None:
            message += f" (exit code: {exit_code})"
        if stderr:
            message += f"\n{stderr}"
        super().__init__(message)


class SecurityViolationError(CoTerException):
    """
    Violation de sécurité détectée

    Levée quand:
    - Une commande dangereuse est tentée
    - Une commande bloquée est détectée
    - Injection de commande suspectée
    """
    def __init__(self, command: str, reason: str, risk_level: str = "high"):
        self.command = command
        self.reason = reason
        self.risk_level = risk_level
        message = f"Sécurité: {reason}\nCommande: {command}"
        super().__init__(message)


class PTYShellError(CoTerException):
    """
    Erreur liée au shell PTY persistant

    Levée quand:
    - Le shell PTY ne peut pas démarrer
    - Le shell PTY meurt inopinément
    - Problème de communication avec le shell
    """
    def __init__(self, message: str, shell_pid: int = None):
        self.shell_pid = shell_pid
        full_message = f"Erreur PTY: {message}"
        if shell_pid:
            full_message += f" (PID: {shell_pid})"
        super().__init__(full_message)


class StreamingError(CoTerException):
    """
    Erreur lors du streaming IA

    Levée quand:
    - Le générateur de streaming échoue
    - Corruption de données dans le stream
    - Interruption du stream
    """
    def __init__(self, message: str, partial_data: str = None):
        self.partial_data = partial_data
        super().__init__(f"Erreur de streaming: {message}")


class ParsingError(CoTerException):
    """
    Erreur lors du parsing de la réponse IA

    Levée quand:
    - La réponse IA est mal formatée
    - Les balises sont invalides
    - Impossible d'extraire la commande
    """
    def __init__(self, message: str, raw_response: str = None):
        self.raw_response = raw_response
        super().__init__(f"Erreur de parsing: {message}")


class CacheError(CoTerException):
    """
    Erreur liée au cache

    Levée quand:
    - Le cache ne peut pas être initialisé
    - Erreur d'écriture/lecture du cache
    - Cache corrompu
    """
    pass


class AgentError(CoTerException):
    """
    Erreur dans le mode agent autonome

    Levée quand:
    - L'agent ne peut pas générer de plan
    - Échec d'exécution d'une étape
    - Arrêt forcé de l'agent
    """
    def __init__(self, message: str, step_number: int = None):
        self.step_number = step_number
        full_message = message
        if step_number is not None:
            full_message = f"[Étape {step_number}] {message}"
        super().__init__(full_message)


class ValidationError(CoTerException):
    """
    Erreur de validation des données

    Levée quand:
    - Données d'entrée invalides
    - Format incorrect
    - Valeurs hors limites
    """
    def __init__(self, field: str, value: any, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        message = f"Validation échouée pour '{field}': {reason}"
        if value is not None:
            message += f" (valeur: {value})"
        super().__init__(message)


class ConfigurationError(CoTerException):
    """
    Erreur de configuration

    Levée quand:
    - Fichier de configuration invalide
    - Paramètre manquant ou invalide
    - Conflit de configuration
    """
    pass
