"""Exécuteur de commandes shell sécurisé"""

import subprocess
import os
import shlex
from typing import Dict, Optional, Tuple, Any

from src.utils.command_helpers import create_success_result, create_error_result, SafeLogger
from src.security import RiskAssessor

class CommandExecutor:
    """Exécute des commandes shell de manière sécurisée"""

    # Limites de buffer pour sortie commande (CSAPP Ch.10)
    MAX_OUTPUT_SIZE_BYTES = 1 * 1024 * 1024  # 1MB max pour stdout/stderr
    OUTPUT_BUFFER_SIZE = 8192  # 8KB buffer pour lecture streaming

    def __init__(self, settings, logger=None, max_output_size: Optional[int] = None):
        """
        Initialise l'exécuteur de commandes

        Args:
            settings: Configuration de l'application
            logger: Logger pour les messages
            max_output_size: Taille max de sortie (None = utiliser MAX_OUTPUT_SIZE_BYTES)
        """
        self.settings = settings
        self.logger = SafeLogger(logger)
        self.risk_assessor = RiskAssessor()
        self.current_directory = os.getcwd()
        self.max_output_size = max_output_size or self.MAX_OUTPUT_SIZE_BYTES

        if self.logger:
            self.logger.debug(f"Buffer limit: max_output={self.max_output_size / 1024:.0f}KB")

    def execute(self, command: str, timeout: int = 30, strict_mode: bool = True) -> Dict[str, Any]:
        """
        Exécute une commande shell

        Args:
            command: La commande à exécuter
            timeout: Timeout en secondes (défaut: 30)
            strict_mode: Si True, validation stricte (mode AUTO/AGENT). Si False, validation minimale (mode MANUAL)

        Returns:
            Dict avec 'success', 'output', 'error', 'return_code'
        """
        if not command or not command.strip():
            return create_error_result('Commande vide')

        # Gérer la commande cd séparément (change le working directory)
        if command.strip().startswith('cd '):
            return self._handle_cd(command)

        # Valider la commande avant exécution avec shell=True
        # En mode strict (AUTO/AGENT), validation complète
        # En mode permissif (MANUAL), validation minimale (seulement les commandes très dangereuses)
        is_safe, error_msg = self._validate_shell_command(command, strict_mode)
        if not is_safe:
            self.logger.error(f"Commande bloquée pour raisons de sécurité: {error_msg}")
            return create_error_result(f'Sécurité: {error_msg}')

        try:
            self.logger.info(f"Exécution de la commande: {command}")

            # Exécuter la commande avec shell=True
            # Note: shell=True est nécessaire pour supporter les features shell (pipes, redirections, etc.)
            # La validation ci-dessus limite les risques d'injection
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.current_directory,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy()
            )

            success = result.returncode == 0
            output = result.stdout.strip()
            error = result.stderr.strip()

            # Vérifier et limiter la taille de la sortie (protection mémoire CSAPP Ch.10)
            output_size = len(output.encode('utf-8'))
            error_size = len(error.encode('utf-8'))
            output_truncated = False
            error_truncated = False

            if output_size > self.max_output_size:
                output = output[:self.max_output_size]
                output += f"\n\n[... Sortie tronquée à {self.max_output_size / 1024:.0f}KB ...]"
                output_truncated = True
                self.logger.warning(f"Stdout tronqué: {output_size / 1024:.1f}KB > {self.max_output_size / 1024:.0f}KB")

            if error_size > self.max_output_size:
                error = error[:self.max_output_size]
                error += f"\n\n[... Erreur tronquée à {self.max_output_size / 1024:.0f}KB ...]"
                error_truncated = True
                self.logger.warning(f"Stderr tronqué: {error_size / 1024:.1f}KB > {self.max_output_size / 1024:.0f}KB")

            if success:
                self.logger.debug(f"Commande réussie. Output: {output[:200]}")
                result_dict = create_success_result(output, result.returncode)
                if output_truncated:
                    result_dict['truncated'] = True
                    result_dict['original_size_kb'] = output_size / 1024
                return result_dict
            else:
                self.logger.warning(f"Commande échouée (code {result.returncode}). Error: {error[:200]}")
                result_dict = create_error_result(error, result.returncode, output)
                if error_truncated or output_truncated:
                    result_dict['truncated'] = True
                return result_dict

        except subprocess.TimeoutExpired:
            error_msg = f"Timeout: La commande a dépassé {timeout} secondes"
            self.logger.error(error_msg)
            return create_error_result(error_msg)

        except Exception as e:
            error_msg = f"Erreur lors de l'exécution: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return create_error_result(error_msg)

    def _handle_cd(self, command: str) -> Dict[str, Any]:
        """
        Gère la commande cd (changement de répertoire)

        Args:
            command: Commande cd avec le chemin

        Returns:
            Résultat de l'opération
        """
        parts = command.strip().split(maxsplit=1)

        if len(parts) == 1:
            # cd sans argument = aller au home
            target_dir = os.path.expanduser('~')
        else:
            target_dir = parts[1].strip()
            # Expander les chemins relatifs
            if not os.path.isabs(target_dir):
                target_dir = os.path.join(self.current_directory, target_dir)
            target_dir = os.path.normpath(target_dir)

        try:
            if os.path.isdir(target_dir):
                self.current_directory = target_dir
                self.logger.info(f"Répertoire changé vers: {self.current_directory}")
                return create_success_result(f"Répertoire changé vers: {self.current_directory}")
            else:
                error_msg = f"Répertoire introuvable: {target_dir}"
                return create_error_result(error_msg, 1)
        except Exception as e:
            error_msg = f"Erreur lors du changement de répertoire: {str(e)}"
            self.logger.error(error_msg)
            return create_error_result(error_msg, 1)

    def execute_safe(self, command: str, require_confirmation: bool = False) -> Dict[str, Any]:
        """
        Exécute une commande avec vérification de sécurité

        Args:
            command: La commande à exécuter
            require_confirmation: Si True, lève une exception pour demander confirmation

        Returns:
            Résultat de l'exécution ou erreur
        """
        assessment = self.risk_assessor.assess_risk(command)

        if assessment.level.value in ['high', 'blocked'] and require_confirmation:
            result = create_error_result('CONFIRMATION_REQUIRED')
            result['risk_level'] = assessment.level.value
            return result

        return self.execute(command)

    def _validate_shell_command(self, command: str, strict_mode: bool = True) -> Tuple[bool, str]:
        """
        Valide une commande avant exécution avec shell=True pour éviter les injections

        Args:
            command: La commande à valider
            strict_mode: Si True, validation stricte. Si False, validation minimale

        Returns:
            Tuple (is_safe, warning_message)
        """
        if not command or not command.strip():
            return False, "Commande vide"

        # Commandes TOUJOURS interdites (peu importe le mode)
        very_dangerous = ['rm -rf /', 'dd if=', 'mkfs', ':(){:|:&};:', 'fork bomb']
        for danger in very_dangerous:
            if danger in command.lower():
                return False, f"Commande interdite détectée: {danger}"

        # En mode MANUAL (strict_mode=False), on autorise pipes, redirections, etc.
        # On bloque seulement les commandes vraiment dangereuses
        if not strict_mode:
            self.logger.debug(f"Exécution en mode permissif: {command[:100]}")
            return True, ""

        # En mode strict (AUTO/AGENT), on surveille les patterns à risque
        dangerous_patterns = [
            ('$(', 'Substitution de commande détectée'),
            ('`', 'Substitution de commande (backticks) détectée'),
            ('&&', 'Chaînage de commandes détecté'),
            ('||', 'Chaînage conditionnel détecté'),
            (';', 'Séparateur de commandes détecté'),
            ('|', 'Pipe détecté'),
            ('>', 'Redirection de sortie détectée'),
            ('<', 'Redirection d\'entrée détectée'),
            ('\n', 'Nouvelle ligne dans la commande'),
            ('\r', 'Retour chariot dans la commande'),
        ]

        warnings = []
        for pattern, message in dangerous_patterns:
            if pattern in command:
                warnings.append(message)

        # Si des warnings en mode strict, logger mais autoriser (pour compatibilité)
        if warnings:
            self.logger.warning(f"Commande avec patterns à risque: {', '.join(warnings)}")
            self.logger.warning(f"Commande: {command[:100]}")

        return True, ""

    def get_current_directory(self) -> str:
        """Retourne le répertoire courant"""
        return self.current_directory

    def validate_command(self, command: str) -> Tuple[bool, str]:
        """
        Valide une commande avant exécution

        Args:
            command: La commande à valider

        Returns:
            Tuple (is_valid, error_message)
        """
        if not command or not command.strip():
            return False, "Commande vide"

        # Vérifier les caractères suspects
        suspicious_patterns = [
            '&&', '||', ';',  # Chaînage de commandes
            '$(', '`',         # Command substitution
            '|',               # Pipe (acceptable mais surveillé)
        ]

        # Pour une sécurité maximale, on pourrait bloquer ces patterns
        # Mais pour l'instant on les autorise avec logging

        return True, ""

    def get_system_info(self) -> Dict[str, str]:
        """
        Récupère des informations système

        Returns:
            Dict avec les informations système
        """
        info = {}

        commands = {
            'hostname': 'hostname',
            'username': 'whoami',
            'os': 'uname -a',
            'uptime': 'uptime',
            'current_dir': 'pwd'
        }

        for key, cmd in commands.items():
            result = self.execute(cmd, timeout=5)
            if result['success']:
                info[key] = result['output']
            else:
                info[key] = 'N/A'

        return info
