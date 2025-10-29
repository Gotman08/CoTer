"""Module de sécurité pour la validation des commandes"""

import re
from typing import Tuple, List, Dict, Any
from collections import deque
from datetime import datetime, timedelta

class SecurityValidator:
    """Validateur de sécurité pour les commandes shell"""

    # Commandes absolument interdites
    BLACKLISTED_COMMANDS = [
        'dd if=/dev/zero',     # Effacer le disque
        'mkfs',                # Formater un disque
        'fdisk',               # Partitionnement dangereux
        ':(){ :|:& };:',       # Fork bomb
        'rm -rf /',            # Suppression récursive de la racine
        'chmod -R 777 /',      # Permissions dangereuses sur tout le système
        'wget http',           # Téléchargement non sécurisé
        'curl http',           # Téléchargement non sécurisé
    ]

    # Commandes nécessitant une confirmation explicite
    HIGH_RISK_COMMANDS = [
        'rm', 'rmdir', 'dd', 'shutdown', 'reboot', 'poweroff', 'halt',
        'init', 'kill', 'killall', 'pkill', 'systemctl stop', 'systemctl disable',
        'iptables', 'ufw', 'firewall-cmd', 'apt remove', 'apt purge', 'pip uninstall'
    ]

    # Commandes sûres (whitelist)
    SAFE_COMMANDS = [
        'ls', 'pwd', 'cd', 'cat', 'less', 'more', 'head', 'tail',
        'grep', 'find', 'echo', 'date', 'whoami', 'hostname',
        'df', 'du', 'free', 'top', 'htop', 'ps', 'uptime',
        'git status', 'git log', 'git diff', 'npm list', 'pip list'
    ]

    # Patterns dangereux
    DANGEROUS_PATTERNS = [
        r'rm\s+.*-rf\s+/',           # rm -rf sur la racine ou système
        r'rm\s+.*-rf\s+/\w+',        # rm -rf sur dossiers système
        r'>\s*/dev/sd[a-z]',         # Écriture directe sur disque
        r'dd\s+.*of=/dev/',          # dd vers un device
        r'mkfs\.',                   # Création de filesystem
        r'chmod\s+-R\s+777',         # Permissions dangereuses récursives
        r'chown\s+-R\s+.*\s+/',      # Changement propriétaire récursif système
        r'eval\s+\$',                # Injection de commande via eval
        r'bash\s+-c',                # Exécution de bash indirecte
        r'curl.*\|\s*bash',          # Pipe vers bash (dangereux)
        r'wget.*\|\s*sh',            # Pipe vers shell (dangereux)
    ]

    # Dossiers système à protéger
    PROTECTED_PATHS = [
        '/bin', '/sbin', '/usr/bin', '/usr/sbin',
        '/etc', '/boot', '/sys', '/proc', '/dev'
    ]

    def __init__(self, logger=None):
        """
        Initialise le validateur de sécurité

        Args:
            logger: Logger pour les messages
        """
        self.logger = logger

        # Phase 2: Historique des commandes pour détection de patterns suspects
        self.command_history = deque(maxlen=100)  # Garde les 100 dernières commandes

        # Compteurs pour détection d'abus
        self.failed_commands_count = 0
        self.high_risk_commands_count = 0
        self.last_reset = datetime.now()

    def validate_command(self, command: str) -> Tuple[bool, str, str]:
        """
        Valide une commande pour la sécurité

        Args:
            command: La commande à valider

        Returns:
            Tuple (is_valid, risk_level, reason)
            - is_valid: True si la commande peut être exécutée
            - risk_level: 'low', 'medium', 'high', ou 'blocked'
            - reason: Raison du blocage ou avertissement
        """
        if not command or not command.strip():
            return False, 'blocked', "Commande vide"

        command_lower = command.lower().strip()

        # Vérifier la liste noire
        for blacklisted in self.BLACKLISTED_COMMANDS:
            if blacklisted.lower() in command_lower:
                if self.logger:
                    self.logger.warning(f"Commande bloquée (liste noire): {command}")
                return False, 'blocked', f"Commande interdite détectée: {blacklisted}"

        # Vérifier les patterns dangereux
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                if self.logger:
                    self.logger.warning(f"Pattern dangereux détecté: {command}")
                return False, 'blocked', "Pattern dangereux détecté dans la commande"

        # Vérifier les chemins protégés
        for protected_path in self.PROTECTED_PATHS:
            if f" {protected_path}" in command or f"={protected_path}" in command:
                if any(risky in command for risky in ['rm', 'rmdir', 'chmod', 'chown']):
                    if self.logger:
                        self.logger.warning(f"Tentative de modification de chemin protégé: {command}")
                    return False, 'blocked', f"Modification de {protected_path} interdite"

        # Vérifier les commandes à haut risque
        cmd_base = command.split()[0] if command else ""
        for high_risk in self.HIGH_RISK_COMMANDS:
            if cmd_base == high_risk or command.startswith(high_risk):
                return True, 'high', f"Commande à haut risque: {high_risk}"

        # Vérifier la présence de sudo
        if 'sudo' in command_lower:
            return True, 'high', "Utilisation de sudo détectée"

        # Vérifier les pipes et redirections
        if '|' in command or '>' in command or '<' in command:
            return True, 'medium', "Utilisation de pipes ou redirections"

        # Commande semble sûre
        return True, 'low', "Commande sûre"

    def requires_confirmation(self, risk_level: str) -> bool:
        """
        Détermine si une commande nécessite une confirmation

        Args:
            risk_level: Niveau de risque ('low', 'medium', 'high', 'blocked')

        Returns:
            True si confirmation requise
        """
        return risk_level in ['high', 'medium']

    def get_confirmation_message(self, command: str, risk_level: str, reason: str) -> str:
        """
        Génère un message de confirmation pour l'utilisateur

        Args:
            command: La commande à exécuter
            risk_level: Niveau de risque
            reason: Raison du risque

        Returns:
            Message de confirmation
        """
        if risk_level == 'high':
            emoji = "⚠️ "
            level_text = "DANGER"
        elif risk_level == 'medium':
            emoji = "⚡"
            level_text = "ATTENTION"
        else:
            emoji = "ℹ️"
            level_text = "INFO"

        message = f"""
{emoji} {level_text} {emoji}
Commande: {command}
Raison: {reason}

Voulez-vous vraiment exécuter cette commande? (oui/non)"""

        return message

    def sanitize_output(self, output: str, max_length: int = 5000) -> str:
        """
        Nettoie et limite la taille de la sortie

        Args:
            output: Sortie à nettoyer
            max_length: Longueur maximale

        Returns:
            Sortie nettoyée
        """
        if not output:
            return ""

        # Limiter la longueur
        if len(output) > max_length:
            output = output[:max_length] + "\n... (sortie tronquée)"

        return output

    def is_safe_for_automation(self, command: str) -> bool:
        """
        Vérifie si une commande peut être exécutée en mode automatique

        Args:
            command: Commande à vérifier

        Returns:
            True si la commande peut être automatisée sans confirmation
        """
        is_valid, risk_level, _ = self.validate_command(command)
        return is_valid and risk_level == 'low'

    def calculate_risk_score(self, command: str) -> int:
        """
        Calcule un score de risque numérique pour une commande (0-100)

        Args:
            command: Commande à analyser

        Returns:
            Score de risque (0 = sûr, 100 = très dangereux)
        """
        score = 0
        command_lower = command.lower().strip()

        # Vérifier la whitelist (commandes sûres)
        cmd_base = command.split()[0] if command else ""
        if any(safe in command for safe in self.SAFE_COMMANDS):
            return 0  # Commande whitelistée = sûre

        # Blacklist = score maximum
        for blacklisted in self.BLACKLISTED_COMMANDS:
            if blacklisted.lower() in command_lower:
                return 100

        # Patterns dangereux = +50
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                score += 50

        # Commandes à haut risque = +40
        for high_risk in self.HIGH_RISK_COMMANDS:
            if cmd_base == high_risk or command.startswith(high_risk):
                score += 40
                break

        # Chemins protégés = +30
        for protected_path in self.PROTECTED_PATHS:
            if protected_path in command:
                if any(risky in command for risky in ['rm', 'rmdir', 'chmod', 'chown']):
                    score += 30
                    break

        # Sudo = +20
        if 'sudo' in command_lower:
            score += 20

        # Force flags = +15
        if '-f' in command or '--force' in command:
            score += 15

        # Recursive flags = +10
        if '-r' in command or '-R' in command or '--recursive' in command:
            score += 10

        # Pipes et redirections = +10
        if '|' in command:
            score += 10
        if '>' in command or '>>' in command:
            score += 5

        # Network operations = +15
        if any(net in command_lower for net in ['wget', 'curl', 'nc', 'netcat', 'telnet']):
            score += 15

        # Package management = +10
        if any(pkg in command_lower for pkg in ['apt', 'yum', 'dnf', 'pacman', 'pip install']):
            score += 10

        return min(score, 100)  # Cap à 100

    def detect_suspicious_patterns(self) -> List[str]:
        """
        Analyse l'historique pour détecter des patterns suspects

        Returns:
            Liste des alertes de sécurité
        """
        alerts = []

        # Réinitialiser les compteurs si nécessaire (toutes les heures)
        if datetime.now() - self.last_reset > timedelta(hours=1):
            self.failed_commands_count = 0
            self.high_risk_commands_count = 0
            self.last_reset = datetime.now()

        # Trop de commandes à haut risque en peu de temps
        if self.high_risk_commands_count > 10:
            alerts.append("⚠️  Nombre élevé de commandes à haut risque détecté")

        # Trop d'échecs
        if self.failed_commands_count > 20:
            alerts.append("⚠️  Nombre élevé de commandes échouées détecté")

        # Analyser les dernières commandes pour détecter des séquences suspectes
        if len(self.command_history) >= 3:
            recent = list(self.command_history)[-3:]

            # Séquence: recherche de fichiers sensibles puis suppression
            if any('find' in cmd for cmd in recent[:2]) and any('rm' in cmd for cmd in recent[2:]):
                alerts.append("⚠️  Séquence suspecte détectée: recherche puis suppression")

            # Multiples tentatives de sudo
            sudo_count = sum(1 for cmd in recent if 'sudo' in cmd)
            if sudo_count >= 2:
                alerts.append("⚠️  Multiples commandes sudo détectées")

        return alerts

    def record_command_execution(self, command: str, success: bool, risk_level: str):
        """
        Enregistre une commande dans l'historique pour analyse

        Args:
            command: Commande exécutée
            success: Si la commande a réussi
            risk_level: Niveau de risque
        """
        # Ajouter à l'historique
        self.command_history.append({
            'command': command,
            'success': success,
            'risk_level': risk_level,
            'timestamp': datetime.now()
        })

        # Incrémenter les compteurs
        if not success:
            self.failed_commands_count += 1

        if risk_level == 'high':
            self.high_risk_commands_count += 1

    def get_security_report(self) -> Dict[str, Any]:
        """
        Génère un rapport de sécurité

        Returns:
            Dict avec les statistiques de sécurité
        """
        total_commands = len(self.command_history)

        if total_commands == 0:
            return {
                'total_commands': 0,
                'message': 'Aucune commande exécutée'
            }

        # Compter par niveau de risque
        low_risk = sum(1 for cmd in self.command_history if cmd['risk_level'] == 'low')
        medium_risk = sum(1 for cmd in self.command_history if cmd['risk_level'] == 'medium')
        high_risk = sum(1 for cmd in self.command_history if cmd['risk_level'] == 'high')
        blocked = sum(1 for cmd in self.command_history if cmd['risk_level'] == 'blocked')

        # Taux de réussite
        successful = sum(1 for cmd in self.command_history if cmd['success'])
        success_rate = (successful / total_commands * 100) if total_commands > 0 else 0

        # Détecter des patterns suspects
        alerts = self.detect_suspicious_patterns()

        return {
            'total_commands': total_commands,
            'low_risk': low_risk,
            'medium_risk': medium_risk,
            'high_risk': high_risk,
            'blocked': blocked,
            'success_rate': round(success_rate, 1),
            'failed_count': self.failed_commands_count,
            'high_risk_count': self.high_risk_commands_count,
            'alerts': alerts,
            'history_size': len(self.command_history)
        }

    def is_network_command(self, command: str) -> bool:
        """
        Vérifie si une commande implique des opérations réseau

        Args:
            command: Commande à vérifier

        Returns:
            True si c'est une commande réseau
        """
        network_keywords = [
            'wget', 'curl', 'nc', 'netcat', 'telnet', 'ssh', 'scp', 'ftp',
            'ping', 'traceroute', 'nmap', 'dig', 'nslookup', 'host'
        ]

        command_lower = command.lower()
        return any(keyword in command_lower for keyword in network_keywords)
