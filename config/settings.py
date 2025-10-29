"""Configuration du Terminal IA"""

import os
from pathlib import Path

class Settings:
    """Classe de configuration principale"""

    def __init__(self):
        # Chemins
        self.base_dir = Path(__file__).parent.parent
        self.logs_dir = self.base_dir / "logs"
        self.config_dir = self.base_dir / "config"

        # Configuration Ollama
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama2")
        self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))

        # Configuration du terminal
        self.prompt_symbol = "🤖 IA>"
        self.max_history = 100
        self.auto_confirm_safe_commands = False  # Demander confirmation pour toutes les commandes

        # Commandes autorisées (liste blanche pour sécurité)
        self.safe_commands = [
            "ls", "pwd", "cd", "cat", "echo", "date", "whoami",
            "df", "free", "uptime", "uname", "hostname"
        ]

        # Commandes dangereuses nécessitant une confirmation
        self.dangerous_commands = [
            "rm", "rmdir", "mv", "chmod", "chown", "kill",
            "shutdown", "reboot", "systemctl", "sudo"
        ]

        # Configuration des logs
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = self.logs_dir / "terminal_ia.log"

        # Configuration de l'agent autonome
        self.agent_enabled = True  # Activer le mode agent autonome
        self.agent_max_steps = int(os.getenv("AGENT_MAX_STEPS", "50"))
        self.agent_max_duration_minutes = int(os.getenv("AGENT_MAX_DURATION", "30"))
        self.agent_pause_between_steps = float(os.getenv("AGENT_PAUSE_STEPS", "0.5"))
        self.agent_auto_confirm_plan = False  # Demander confirmation avant exécution

        # Configuration génération de code
        self.code_gen_enabled = True  # Activer génération de code
        self.code_gen_backup = True  # Backup avant modification
        self.code_gen_max_file_size = 100000  # Taille max en caractères

        # Configuration Git
        self.git_auto_init = True  # Initialiser git automatiquement pour nouveaux projets
        self.git_auto_commit = True  # Créer des commits automatiques
        self.git_commit_ai_messages = True  # Utiliser l'IA pour messages de commit

        # Créer les dossiers nécessaires
        self.logs_dir.mkdir(exist_ok=True)

    def is_safe_command(self, command: str) -> bool:
        """Vérifie si une commande est considérée comme sûre"""
        cmd_base = command.split()[0] if command else ""
        return cmd_base in self.safe_commands

    def is_dangerous_command(self, command: str) -> bool:
        """Vérifie si une commande est dangereuse"""
        cmd_base = command.split()[0] if command else ""
        return cmd_base in self.dangerous_commands
