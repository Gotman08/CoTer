"""
Gestionnaire de prompt avec historique navigable et auto-complétion
Utilise prompt_toolkit pour une expérience terminal moderne
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Callable

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion, PathCompleter, WordCompleter, merge_completers
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

logger = logging.getLogger(__name__)


class CoTermCompleter(Completer):
    """
    Auto-complétion personnalisée pour CoTer

    Complète :
    - Commandes système (PATH)
    - Commandes CoTer (/manual, /auto, /fast, /agent, etc.)
    - Fichiers et dossiers
    """

    def __init__(self):
        self.coter_commands = [
            '/help', '/manual', '/auto', '/fast', '/agent',
            '/clear', '/history', '/models', '/info',
            '/cache', '/hardware', '/rollback', '/security',
            '/corrections', '/status', '/templates', '/quit',
            '/pause', '/resume', '/stop'
        ]

        # Completer pour les commandes CoTer
        self.slash_completer = WordCompleter(
            self.coter_commands,
            ignore_case=True,
            sentence=True
        )

        # Completer pour les fichiers/dossiers
        self.path_completer = PathCompleter(expanduser=True)

        logger.debug(f"Completer initialisé avec {len(self.coter_commands)} commandes CoTer")

    def get_completions(self, document, complete_event):
        """
        Génère les suggestions d'auto-complétion

        Args:
            document: Document courant
            complete_event: Événement de complétion

        Yields:
            Completions possibles
        """
        text = document.text_before_cursor

        # Si on commence par '/', proposer d'abord les commandes CoTer
        if text.startswith('/'):
            # Priorité aux commandes slash
            for completion in self.slash_completer.get_completions(document, complete_event):
                yield completion

        # Toujours proposer aussi les fichiers/dossiers (sauf si on est en pleine commande slash)
        # Cela permet de compléter les arguments de commandes
        if not text.startswith('/') or ' ' in text:
            for completion in self.path_completer.get_completions(document, complete_event):
                yield completion


class PromptManager:
    """
    Gestionnaire de prompt interactif avec prompt_toolkit

    Features:
    - Historique navigable avec ↑↓
    - Recherche d'historique avec Ctrl+R
    - Auto-complétion avec Tab
    - Auto-suggestions
    - Keybindings personnalisés
    """

    def __init__(self, history_file: Optional[str] = None, enable_suggestions: bool = True):
        """
        Initialise le gestionnaire de prompt

        Args:
            history_file: Fichier d'historique (.coter_history par défaut)
            enable_suggestions: Activer les auto-suggestions
        """
        # Fichier d'historique
        if history_file is None:
            history_file = str(Path.home() / '.coter_history')

        self.history_file = history_file
        self.enable_suggestions = enable_suggestions

        # Créer les key bindings personnalisés
        key_bindings = self._create_key_bindings()

        # Créer la session prompt_toolkit
        self.session = PromptSession(
            history=FileHistory(self.history_file),
            auto_suggest=AutoSuggestFromHistory() if enable_suggestions else None,
            completer=CoTermCompleter(),
            complete_while_typing=False,  # Compléter seulement sur Tab
            enable_history_search=True,  # Ctrl+R pour recherche
            mouse_support=False,  # Pas de support souris (terminal)
            key_bindings=key_bindings,  # Bindings personnalisés
            style=self._get_style()
        )

        logger.info(f"PromptManager initialisé - Historique: {history_file}, Tab completion activée")

    def _create_key_bindings(self) -> KeyBindings:
        """
        Crée les key bindings personnalisés pour le prompt

        Returns:
            KeyBindings configurés
        """
        kb = KeyBindings()

        # Tab: Déclencher la complétion
        @kb.add('tab')
        def _(event):
            """
            Gère l'appui sur Tab pour l'auto-complétion
            """
            buffer = event.current_buffer

            # Si des complétions sont disponibles, passer à la suivante
            if buffer.complete_state:
                buffer.complete_next()
            else:
                # Sinon, démarrer la complétion
                buffer.start_completion()

        logger.debug("Key bindings configurés: Tab pour auto-complétion")
        return kb

    def _get_style(self) -> Style:
        """
        Style personnalisé pour le prompt

        Returns:
            Style prompt_toolkit
        """
        return Style.from_dict({
            # Style pour les suggestions automatiques
            'auto-suggestion': 'fg:#666666',

            # Style pour la complétion
            'completion-menu.completion': 'bg:#008888 #ffffff',
            'completion-menu.completion.current': 'bg:#00aaaa #000000',

            # Style pour la recherche
            'search': 'bg:#884444',
            'search.current': 'bg:#aa6666',
        })

    def prompt(self, message: str = "", default: str = "") -> str:
        """
        Affiche un prompt et attend l'entrée utilisateur

        Args:
            message: Message du prompt
            default: Valeur par défaut

        Returns:
            Entrée utilisateur (string)
        """
        try:
            # Utiliser le message tel quel (prompt_toolkit accepte les strings simples)
            formatted_message = message if message else ''

            result = self.session.prompt(
                formatted_message,
                default=default
            )

            return result

        except (EOFError, KeyboardInterrupt) as e:
            # Ctrl+D ou Ctrl+C
            logger.debug(f"Prompt interrompu: {type(e).__name__}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors du prompt: {e}", exc_info=True)
            # Fallback sur input() basique
            return input(message)

    def clear_history(self):
        """Efface l'historique des commandes"""
        try:
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
                logger.info(f"Historique effacé: {self.history_file}")
        except Exception as e:
            logger.error(f"Erreur lors de l'effacement de l'historique: {e}")

    def get_history(self, limit: int = 100) -> List[str]:
        """
        Récupère l'historique des commandes

        Args:
            limit: Nombre maximum de commandes à retourner

        Returns:
            Liste des commandes (les plus récentes en dernier)
        """
        try:
            if not os.path.exists(self.history_file):
                return []

            with open(self.history_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Nettoyer et limiter
            history = [line.strip() for line in lines if line.strip()]
            return history[-limit:] if len(history) > limit else history

        except Exception as e:
            logger.error(f"Erreur lors de la lecture de l'historique: {e}")
            return []

    def add_to_history(self, command: str):
        """
        Ajoute manuellement une commande à l'historique

        Args:
            command: Commande à ajouter
        """
        # prompt_toolkit gère déjà l'historique automatiquement,
        # mais cette méthode permet d'ajouter des commandes programmatiquement
        try:
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(f"{command}\n")
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout à l'historique: {e}")

    def __repr__(self):
        return f"PromptManager(history='{self.history_file}', suggestions={self.enable_suggestions})"


def create_prompt_manager(history_file: Optional[str] = None) -> PromptManager:
    """
    Factory function pour créer un PromptManager

    Args:
        history_file: Fichier d'historique personnalisé

    Returns:
        Instance de PromptManager
    """
    return PromptManager(history_file=history_file)
