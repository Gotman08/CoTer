"""
Risk Assessor - Évaluation centralisée des risques des commandes

Consolide les 4 implémentations précédentes trouvées dans:
- command_executor.py (_assess_risk)
- command_parser.py (_assess_risk)
- security.py (validate_command et calculate_risk_score)
"""

import re
from enum import Enum
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


class RiskLevel(Enum):
    """Niveaux de risque des commandes"""
    BLOCKED = "blocked"      # Commande interdite (rm -rf /, fork bomb, etc.)
    HIGH = "high"           # Risque élevé (rm, sudo, dd, etc.)
    MEDIUM = "medium"       # Risque moyen (chmod, chown, kill, etc.)
    LOW = "low"             # Risque faible (commandes sûres)
    SAFE = "safe"           # Commandes totalement sûres (ls, cd, pwd, etc.)

    def __str__(self) -> str:
        return self.value


@dataclass
class RiskAssessment:
    """
    Résultat d'une évaluation de risque

    Attributes:
        level: Niveau de risque (RiskLevel)
        score: Score numérique 0-100 (100 = plus dangereux)
        reasons: Liste des raisons du niveau de risque
        is_safe_for_automation: Peut être exécuté automatiquement sans confirmation
        blocked: True si la commande doit être bloquée complètement
    """
    level: RiskLevel
    score: int
    reasons: List[str]
    is_safe_for_automation: bool
    blocked: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour compatibilité"""
        return {
            'level': self.level.value,
            'score': self.score,
            'reasons': self.reasons,
            'is_safe_for_automation': self.is_safe_for_automation,
            'blocked': self.blocked
        }


class RiskAssessor:
    """
    Évaluateur centralisé de risques pour les commandes shell

    Consolide toute la logique de sécurité en un seul endroit.
    Élimine la duplication entre command_executor, command_parser et security.
    """

    # Commandes TOUJOURS bloquées (risque extrême)
    BLOCKED_COMMANDS = [
        'rm -rf /',
        'rm -rf ~',
        'rm -rf *',
        'dd if=/dev/zero',
        'dd if=/dev/random',
        'mkfs',
        'mkfs.ext',
        ':(){:|:&};:',  # Fork bomb
        'fork bomb',
        '>(){ :|:& };:',  # Variant fork bomb
    ]

    # Commandes à haut risque (confirmation requise)
    HIGH_RISK_COMMANDS = [
        'rm', 'rmdir', 'rm -r', 'rm -f',
        'dd',
        'shutdown', 'reboot', 'poweroff', 'halt',
        'mkfs', 'fdisk', 'parted',
        'kill -9', 'killall',
        'chmod 777', 'chmod -R 777',
        'format', 'del /f',
    ]

    # Commandes à risque moyen (logging renforcé)
    MEDIUM_RISK_COMMANDS = [
        'chmod', 'chown', 'chgrp',
        'kill', 'pkill',
        'mv', 'cp -r',
        'wget', 'curl -O',
        'git push --force',
        'docker rm', 'docker stop',
    ]

    # Commandes totalement sûres (pas de risque)
    SAFE_COMMANDS = [
        'ls', 'dir', 'll', 'la',
        'cd', 'pwd',
        'cat', 'less', 'more', 'head', 'tail',
        'echo', 'printf',
        'date', 'time', 'uptime',
        'whoami', 'hostname',
        'ps', 'top', 'htop',
        'df', 'du',
        'which', 'whereis', 'type',
        'history',
        'help', 'man', 'info',
        'grep', 'find', 'locate',
        'wc', 'sort', 'uniq',
        'git status', 'git log', 'git diff',
    ]

    # Patterns dangereux
    DANGEROUS_PATTERNS = [
        (r'sudo\s+(rm|dd|mkfs|shutdown)', 'Commande système avec sudo'),
        (r'-rf\s+/', 'Suppression récursive forcée depuis racine'),
        (r'-rf\s+~', 'Suppression récursive forcée du home'),
        (r'-rf\s+\*', 'Suppression récursive forcée avec wildcard'),
        (r'>\s*/dev/(sd[a-z]|hd[a-z]|nvme)', 'Écriture directe sur disque'),
        (r'chmod\s+[0-7]{3,4}\s+/', 'Chmod récursif depuis racine'),
        (r'chown.*-R.*/', 'Chown récursif depuis racine'),
        (r'\|\s*bash', 'Pipe vers bash (risque d\'injection)'),
        (r'\|\s*sh', 'Pipe vers sh (risque d\'injection)'),
        (r'eval\s+', 'Utilisation d\'eval (risque d\'injection)'),
        (r'exec\s+', 'Utilisation d\'exec'),
        (r':\(\)\{.*\|\:.*\}', 'Fork bomb détectée'),
    ]

    # Chemins protégés
    PROTECTED_PATHS = [
        '/', '/bin', '/sbin', '/boot', '/dev', '/etc', '/lib', '/lib64',
        '/proc', '/sys', '/usr', '/var',
        'C:\\Windows', 'C:\\Program Files', 'C:\\System32',
    ]

    def __init__(self):
        """Initialise le RiskAssessor"""
        pass

    def assess_risk(self, command: str) -> RiskAssessment:
        """
        Évalue le risque d'une commande

        Args:
            command: La commande à évaluer

        Returns:
            RiskAssessment avec niveau, score et raisons
        """
        if not command or not command.strip():
            return RiskAssessment(
                level=RiskLevel.SAFE,
                score=0,
                reasons=["Commande vide"],
                is_safe_for_automation=True,
                blocked=False
            )

        command_lower = command.lower().strip()
        reasons = []
        score = 0

        # 1. Vérifier les commandes bloquées (priorité absolue)
        for blocked_cmd in self.BLOCKED_COMMANDS:
            if blocked_cmd.lower() in command_lower:
                return RiskAssessment(
                    level=RiskLevel.BLOCKED,
                    score=100,
                    reasons=[f"Commande interdite détectée: {blocked_cmd}"],
                    is_safe_for_automation=False,
                    blocked=True
                )

        # 2. Vérifier les patterns dangereux
        for pattern, reason in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                reasons.append(reason)
                score += 30

        # 3. Vérifier les chemins protégés
        for protected_path in self.PROTECTED_PATHS:
            if protected_path in command:
                reasons.append(f"Opération sur chemin protégé: {protected_path}")
                score += 25

        # 4. Extraire la commande de base
        base_command = self._extract_base_command(command)

        # 5. Vérifier contre les listes de commandes
        if self._is_in_command_list(base_command, self.SAFE_COMMANDS):
            # Commande sûre, mais vérifier les modifiers
            if 'sudo' in command_lower:
                score += 20
                reasons.append("Utilisation de sudo")
            else:
                score = max(score, 0)  # Commande sûre
        elif self._is_in_command_list(base_command, self.HIGH_RISK_COMMANDS):
            score += 40
            reasons.append(f"Commande à haut risque: {base_command}")
        elif self._is_in_command_list(base_command, self.MEDIUM_RISK_COMMANDS):
            score += 20
            reasons.append(f"Commande à risque moyen: {base_command}")

        # 6. Vérifier les flags dangereux
        dangerous_flags = ['-rf', '-f', '--force', '-9', '-r', '--recursive']
        for flag in dangerous_flags:
            if flag in command:
                score += 10
                reasons.append(f"Flag dangereux: {flag}")

        # 7. Vérifier sudo
        if 'sudo' in command_lower:
            score += 15
            if "Utilisation de sudo" not in reasons:
                reasons.append("Utilisation de sudo")

        # 8. Déterminer le niveau de risque basé sur le score
        if score >= 80:
            level = RiskLevel.BLOCKED
            blocked = True
            safe_for_automation = False
        elif score >= 50:
            level = RiskLevel.HIGH
            blocked = False
            safe_for_automation = False
        elif score >= 25:
            level = RiskLevel.MEDIUM
            blocked = False
            safe_for_automation = False
        elif score > 0:
            level = RiskLevel.LOW
            blocked = False
            safe_for_automation = True
        else:
            level = RiskLevel.SAFE
            blocked = False
            safe_for_automation = True

        if not reasons:
            reasons = ["Commande standard"]

        return RiskAssessment(
            level=level,
            score=min(score, 100),  # Cap à 100
            reasons=reasons,
            is_safe_for_automation=safe_for_automation,
            blocked=blocked
        )

    def _extract_base_command(self, command: str) -> str:
        """
        Extrait la commande de base (sans arguments)

        Args:
            command: Commande complète

        Returns:
            Commande de base
        """
        # Enlever sudo au début
        cmd = command.strip()
        if cmd.startswith('sudo '):
            cmd = cmd[5:].strip()

        # Prendre le premier mot
        parts = cmd.split()
        if parts:
            return parts[0]
        return ""

    def _is_in_command_list(self, base_command: str, command_list: List[str]) -> bool:
        """
        Vérifie si une commande de base est dans une liste

        Args:
            base_command: Commande de base à vérifier
            command_list: Liste de commandes

        Returns:
            True si trouvée
        """
        base_lower = base_command.lower()

        for cmd in command_list:
            # Support des commandes avec arguments (ex: "git status")
            cmd_parts = cmd.lower().split()
            if cmd_parts[0] == base_lower:
                return True

        return False

    def is_safe(self, command: str) -> bool:
        """
        Vérifie rapidement si une commande est sûre

        Args:
            command: Commande à vérifier

        Returns:
            True si sûre (niveau SAFE ou LOW)
        """
        assessment = self.assess_risk(command)
        return assessment.level in [RiskLevel.SAFE, RiskLevel.LOW]

    def is_blocked(self, command: str) -> bool:
        """
        Vérifie rapidement si une commande est bloquée

        Args:
            command: Commande à vérifier

        Returns:
            True si bloquée
        """
        assessment = self.assess_risk(command)
        return assessment.blocked

    def requires_confirmation(self, command: str) -> bool:
        """
        Vérifie si une commande nécessite une confirmation utilisateur

        Args:
            command: Commande à vérifier

        Returns:
            True si confirmation requise (HIGH ou MEDIUM)
        """
        assessment = self.assess_risk(command)
        return assessment.level in [RiskLevel.HIGH, RiskLevel.MEDIUM]

    def get_risk_level_str(self, command: str) -> str:
        """
        Retourne le niveau de risque sous forme de string

        Args:
            command: Commande à évaluer

        Returns:
            "safe", "low", "medium", "high", ou "blocked"
        """
        assessment = self.assess_risk(command)
        return assessment.level.value

    def validate_command(self, command: str) -> Tuple[bool, str, str]:
        """
        Valide une commande (compatible avec l'ancienne interface)

        Args:
            command: Commande à valider

        Returns:
            Tuple (is_valid, risk_level, reason)
        """
        assessment = self.assess_risk(command)

        is_valid = not assessment.blocked
        risk_level = assessment.level.value
        reason = "; ".join(assessment.reasons) if assessment.reasons else "OK"

        return is_valid, risk_level, reason
