"""
Shell Engine - Moteur du shell hybride CoTer
Gère les modes MANUAL/AUTO/AGENT et leur état
"""

from enum import Enum
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ShellMode(Enum):
    """
    Modes d'opération du shell CoTer

    MANUAL: Mode shell direct - exécute les commandes sans intervention IA
    AUTO: Mode IA activé - parse le langage naturel via Ollama (ITÉRATIF par défaut)
    FAST: Mode IA one-shot - génère UNE commande optimale et termine
    AGENT: Mode projet autonome - planification multi-étapes avec l'agent
    """
    MANUAL = "manual"
    AUTO = "auto"
    FAST = "fast"
    AGENT = "agent"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, mode_str: str) -> 'ShellMode':
        """Convertit une chaîne en ShellMode"""
        mode_str = mode_str.lower().strip()
        for mode in cls:
            if mode.value == mode_str:
                return mode
        raise ValueError(f"Mode invalide: {mode_str}. Modes valides: {[m.value for m in cls]}")


class ShellEngine:
    """
    Moteur du shell hybride CoTer

    Gère:
    - Le mode actuel (MANUAL/AUTO/AGENT)
    - Les transitions entre modes
    - L'état de session du shell
    - Les statistiques d'utilisation
    """

    def __init__(self, default_mode: ShellMode = ShellMode.MANUAL):
        """
        Initialise le moteur du shell

        Args:
            default_mode: Mode par défaut au démarrage (MANUAL par défaut)
        """
        self._current_mode = default_mode
        self._mode_history = [default_mode]
        self._command_count = {mode: 0 for mode in ShellMode}
        self._session_start_mode = default_mode

        logger.info(f"ShellEngine initialisé en mode {default_mode.value}")

    @property
    def current_mode(self) -> ShellMode:
        """Retourne le mode actuel"""
        return self._current_mode

    @property
    def mode_name(self) -> str:
        """Retourne le nom du mode actuel (string)"""
        return self._current_mode.value

    def switch_mode(self, new_mode: ShellMode) -> bool:
        """
        Bascule vers un nouveau mode

        Args:
            new_mode: Le mode vers lequel basculer

        Returns:
            True si le changement a réussi, False sinon
        """
        if new_mode == self._current_mode:
            logger.info(f"Déjà en mode {new_mode.value}")
            return False

        old_mode = self._current_mode
        self._current_mode = new_mode
        self._mode_history.append(new_mode)

        logger.info(f"Mode changé: {old_mode.value} → {new_mode.value}")
        return True

    def switch_to_manual(self) -> bool:
        """Raccourci pour basculer en mode MANUAL"""
        return self.switch_mode(ShellMode.MANUAL)

    def switch_to_auto(self) -> bool:
        """Raccourci pour basculer en mode AUTO"""
        return self.switch_mode(ShellMode.AUTO)

    def switch_to_fast(self) -> bool:
        """Raccourci pour basculer en mode FAST"""
        return self.switch_mode(ShellMode.FAST)

    def switch_to_agent(self) -> bool:
        """Raccourci pour basculer en mode AGENT"""
        return self.switch_mode(ShellMode.AGENT)

    def increment_command_count(self) -> None:
        """Incrémente le compteur de commandes pour le mode actuel"""
        self._command_count[self._current_mode] += 1

    def get_command_count(self, mode: Optional[ShellMode] = None) -> int:
        """
        Retourne le nombre de commandes exécutées dans un mode

        Args:
            mode: Le mode à interroger (None = mode actuel)

        Returns:
            Nombre de commandes exécutées
        """
        target_mode = mode or self._current_mode
        return self._command_count[target_mode]

    def get_total_command_count(self) -> int:
        """Retourne le nombre total de commandes exécutées (tous modes)"""
        return sum(self._command_count.values())

    def get_statistics(self) -> Dict[str, Any]:
        """
        Retourne les statistiques d'utilisation du shell

        Returns:
            Dictionnaire avec les stats (modes, compteurs, etc.)
        """
        return {
            "current_mode": self._current_mode.value,
            "session_start_mode": self._session_start_mode.value,
            "mode_changes": len(self._mode_history) - 1,
            "command_counts": {mode.value: count for mode, count in self._command_count.items()},
            "total_commands": self.get_total_command_count(),
            "mode_history": [mode.value for mode in self._mode_history]
        }

    def reset_statistics(self) -> None:
        """Réinitialise les statistiques (commandes, historique)"""
        self._command_count = {mode: 0 for mode in ShellMode}
        self._mode_history = [self._current_mode]
        logger.info("Statistiques réinitialisées")

    def is_manual_mode(self) -> bool:
        """Vérifie si on est en mode MANUAL"""
        return self._current_mode == ShellMode.MANUAL

    def is_auto_mode(self) -> bool:
        """Vérifie si on est en mode AUTO"""
        return self._current_mode == ShellMode.AUTO

    def is_fast_mode(self) -> bool:
        """Vérifie si on est en mode FAST"""
        return self._current_mode == ShellMode.FAST

    def is_agent_mode(self) -> bool:
        """Vérifie si on est en mode AGENT"""
        return self._current_mode == ShellMode.AGENT

    def get_prompt_symbol(self) -> str:
        """
        Retourne le symbole de prompt correspondant au mode actuel

        Returns:
            Emoji/symbole représentant le mode
        """
        symbols = {
            ShellMode.MANUAL: "⌨️",   # Clavier pour mode manuel
            ShellMode.AUTO: "🤖",     # Robot pour mode IA
            ShellMode.FAST: "⚡",     # Éclair pour mode rapide
            ShellMode.AGENT: "🏗️"     # Construction pour mode projet
        }
        return symbols[self._current_mode]

    def get_mode_description(self) -> str:
        """
        Retourne une description du mode actuel

        Returns:
            Description textuelle du mode
        """
        descriptions = {
            ShellMode.MANUAL: "Mode Shell Direct - Commandes exécutées sans IA",
            ShellMode.AUTO: "Mode IA Activé - Langage naturel via Ollama (Itératif)",
            ShellMode.FAST: "Mode IA Rapide - Une commande optimale et c'est fini",
            ShellMode.AGENT: "Mode Projet Autonome - Planification multi-étapes"
        }
        return descriptions[self._current_mode]

    def __repr__(self) -> str:
        return f"ShellEngine(mode={self._current_mode.value}, commands={self.get_total_command_count()})"

    def __str__(self) -> str:
        return f"Shell en mode {self._current_mode.value.upper()} ({self.get_command_count()} commandes)"
