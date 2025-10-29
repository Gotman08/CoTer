"""Système de logging pour le Terminal IA"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str = "TerminalIA", debug: bool = False, log_file: str = None) -> logging.Logger:
    """
    Configure et retourne un logger

    Args:
        name: Nom du logger
        debug: Si True, active le mode debug
        log_file: Chemin du fichier de log (optionnel)

    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)

    # Éviter de configurer plusieurs fois
    if logger.handlers:
        return logger

    # Niveau de log
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    # Format des messages
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler pour la console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler pour le fichier si spécifié
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Toujours tout logger dans le fichier
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class CommandLogger:
    """Logger spécialisé pour les commandes exécutées"""

    def __init__(self, log_dir: Path):
        """
        Initialise le logger de commandes

        Args:
            log_dir: Répertoire où sauvegarder les logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"commands_{datetime.now().strftime('%Y%m%d')}.log"

    def log_command(self, user_input: str, command: str, success: bool, output: str = "", error: str = ""):
        """
        Enregistre une commande exécutée

        Args:
            user_input: Demande originale de l'utilisateur
            command: Commande shell générée
            success: Si la commande a réussi
            output: Sortie de la commande
            error: Erreur éventuelle
        """
        timestamp = datetime.now().isoformat()
        status = "SUCCESS" if success else "FAILED"

        log_entry = f"""
{'='*80}
[{timestamp}] {status}
User Input: {user_input}
Command: {command}
Output: {output[:500]}  # Limiter la taille
Error: {error[:500]}
{'='*80}
"""

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def get_recent_commands(self, limit: int = 10) -> list:
        """
        Récupère les commandes récentes

        Args:
            limit: Nombre de commandes à retourner

        Returns:
            Liste des commandes récentes
        """
        if not self.log_file.exists():
            return []

        with open(self.log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parser les entrées (simple split par séparateur)
        entries = content.split('='*80)
        entries = [e.strip() for e in entries if e.strip()]

        return entries[-limit:] if len(entries) > limit else entries
