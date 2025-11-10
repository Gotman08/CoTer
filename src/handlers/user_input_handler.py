"""
Handler pour la gestion des entrées utilisateur et confirmations

Extrait de terminal_interface.py pour centraliser la logique
de validation et confirmation utilisateur.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.terminal_interface import TerminalInterface


class UserInputHandler:
    """
    Gère les interactions avec l'utilisateur (prompts, confirmations, etc.).

    Attributes:
        terminal: Référence vers l'instance TerminalInterface parente
    """

    def __init__(self, terminal: 'TerminalInterface'):
        """
        Initialise le gestionnaire d'entrées utilisateur.

        Args:
            terminal: Instance de TerminalInterface pour accéder aux composants
        """
        self.terminal = terminal
        self.console = terminal.console
        self.logger = terminal.logger
        self.security = terminal.security

    def confirm_command(self, command: str, risk_level: str, reason: str) -> bool:
        """
        Demande confirmation pour une commande à risque.

        Args:
            command: La commande à confirmer
            risk_level: Niveau de risque (low, medium, high)
            reason: Raison du risque

        Returns:
            True si l'utilisateur confirme, False sinon
        """
        message = self.security.get_confirmation_message(command, risk_level, reason)
        print(message)

        while True:
            response = input("\nVotre réponse (oui/non): ").strip().lower()
            if response in ['oui', 'o', 'yes', 'y']:
                return True
            elif response in ['non', 'n', 'no']:
                return False
            else:
                print("Réponse invalide. Tapez 'oui' ou 'non'")

    def prompt_text_input(self, prompt_message: str, allow_empty: bool = False) -> str:
        """
        Demande une entrée textuelle à l'utilisateur.

        Args:
            prompt_message: Message du prompt
            allow_empty: Si True, permet une réponse vide

        Returns:
            Texte saisi par l'utilisateur
        """
        while True:
            user_text = input(f"\n{prompt_message} ").strip()
            if user_text or allow_empty:
                return user_text
            else:
                print("Réponse vide non autorisée. Veuillez saisir du texte.")

    def prompt_yes_no(self, question: str, default: bool = False) -> bool:
        """
        Pose une question oui/non à l'utilisateur.

        Args:
            question: Question à poser
            default: Valeur par défaut si l'utilisateur appuie sur Entrée

        Returns:
            True pour oui, False pour non
        """
        default_text = "oui" if default else "non"
        prompt = f"\n{question} (oui/non, défaut: {default_text}): "

        while True:
            response = input(prompt).strip().lower()

            if not response:
                return default

            if response in ['oui', 'o', 'yes', 'y']:
                return True
            elif response in ['non', 'n', 'no']:
                return False
            else:
                print("Réponse invalide. Tapez 'oui' ou 'non'")
