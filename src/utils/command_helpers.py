"""
Command Helpers - Utilitaires pour réduire la duplication de code
Gestion unifiée des résultats de commandes, logging et historique
"""

from typing import Dict, Any, Callable, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# FACTORY METHODS POUR RÉSULTATS
# ═══════════════════════════════════════════════════════════════

def create_success_result(output: str = "", return_code: int = 0) -> Dict[str, Any]:
    """
    Factory pour créer un résultat de succès standardisé

    Args:
        output: Sortie de la commande
        return_code: Code de retour (défaut: 0)

    Returns:
        Dict standardisé pour succès
    """
    return {
        'success': True,
        'output': output,
        'error': '',
        'return_code': return_code
    }


def create_error_result(error_msg: str, return_code: int = -1, output: str = "") -> Dict[str, Any]:
    """
    Factory pour créer un résultat d'erreur standardisé

    Args:
        error_msg: Message d'erreur
        return_code: Code de retour (défaut: -1)
        output: Sortie partielle éventuelle

    Returns:
        Dict standardisé pour erreur
    """
    return {
        'success': False,
        'output': output,
        'error': error_msg,
        'return_code': return_code
    }


# ═══════════════════════════════════════════════════════════════
# DÉCORATEUR POUR GESTION D'ERREURS
# ═══════════════════════════════════════════════════════════════

def handle_command_errors(error_prefix: str = "Erreur"):
    """
    Décorateur pour gérer les erreurs de manière uniforme

    Usage:
        @handle_command_errors("Erreur mode manuel")
        def _handle_manual_mode(self, user_input: str):
            ...

    Args:
        error_prefix: Préfixe pour le message d'erreur dans les logs

    Returns:
        Décorateur configuré
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except KeyboardInterrupt:
                # Laisser passer les interruptions clavier
                raise
            except Exception as e:
                # Logger l'erreur
                if hasattr(self, 'logger') and self.logger:
                    self.logger.error(f"{error_prefix}: {e}", exc_info=True)

                # Afficher à l'utilisateur
                error_message = f"\n❌ Erreur: {e}"
                if hasattr(self, 'ui') and hasattr(self.ui, 'print_error'):
                    # Utiliser UIFormatter si disponible
                    self.ui.print_error(str(e))
                else:
                    # Fallback sur print standard
                    print(error_message)

                # Retourner None pour signaler l'échec
                return None
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════
# COMMAND RESULT HANDLER - GESTION UNIFIÉE DES RÉSULTATS
# ═══════════════════════════════════════════════════════════════

class CommandResultHandler:
    """
    Gestionnaire unifié pour traiter les résultats de commandes

    Élimine la duplication entre les 3 modes (MANUAL/AUTO/AGENT) en
    centralisant l'affichage, le logging et la sauvegarde dans l'historique.
    """

    def __init__(self, terminal_interface):
        """
        Initialise le gestionnaire

        Args:
            terminal_interface: Référence à l'interface terminal
        """
        self.terminal = terminal_interface

    def handle_result(
        self,
        result: Dict[str, Any],
        command: str,
        user_input: str,
        mode: str
    ) -> None:
        """
        Traite complètement un résultat de commande :
        - Affiche le résultat à l'utilisateur
        - Enregistre dans l'historique persistant
        - Log dans le CommandLogger

        Args:
            result: Résultat de l'exécution (dict avec success, output, error, return_code)
            command: La commande exécutée
            user_input: L'input original de l'utilisateur
            mode: Le mode shell (manual/auto/agent)
        """
        # 1. Afficher le résultat
        self._display_result(result)

        # 2. Ajouter à l'historique persistant
        if hasattr(self.terminal, 'history_manager'):
            self.terminal.history_manager.add_command(
                command=command,
                mode=mode,
                success=result['success']
            )

        # 3. Logger la commande
        if hasattr(self.terminal, 'command_logger'):
            self.terminal.command_logger.log_command(
                user_input=user_input,
                command=command,
                success=result['success'],
                output=result.get('output', ''),
                error=result.get('error', '')
            )

    def _display_result(self, result: Dict[str, Any]) -> None:
        """
        Affiche le résultat d'une commande à l'utilisateur

        Args:
            result: Résultat à afficher
        """
        # Utiliser la méthode existante de terminal_interface si disponible
        if hasattr(self.terminal, '_display_result'):
            self.terminal._display_result(result)
            return

        # Sinon, affichage de base
        if result['success']:
            print(f"\n✅ Commande exécutée avec succès")
            if result.get('output'):
                print(f"\n📤 Sortie:")
                print("─" * 60)
                print(result['output'])
                print("─" * 60)
        else:
            print(f"\n❌ Erreur lors de l'exécution")
            if result.get('error'):
                print(f"\n⚠️  Message d'erreur:")
                print("─" * 60)
                print(result['error'])
                print("─" * 60)


# ═══════════════════════════════════════════════════════════════
# HELPER POUR EXÉCUTION BUILTINS
# ═══════════════════════════════════════════════════════════════

def try_execute_builtin(
    builtins_handler,
    command: str,
    result_handler: CommandResultHandler,
    mode: str
) -> Optional[Dict[str, Any]]:
    """
    Tente d'exécuter une commande builtin

    Args:
        builtins_handler: Instance de BuiltinCommands
        command: Commande à tester
        result_handler: CommandResultHandler pour traiter le résultat
        mode: Mode shell actuel

    Returns:
        Résultat si builtin exécuté, None sinon
    """
    if not builtins_handler.is_builtin(command):
        return None

    result = builtins_handler.execute(command)

    if result is not None:
        # Traiter le résultat via le handler unifié
        result_handler.handle_result(
            result=result,
            command=command,
            user_input=command,
            mode=mode
        )

    return result


# ═══════════════════════════════════════════════════════════════
# HELPER POUR LOGGING SÉCURISÉ
# ═══════════════════════════════════════════════════════════════

class SafeLogger:
    """
    Wrapper pour logger qui gère automatiquement le cas logger=None
    Évite les 100+ checks 'if self.logger:' dans le code
    """

    def __init__(self, logger=None):
        """
        Initialise le SafeLogger

        Args:
            logger: Instance de logger Python (peut être None)
        """
        self._logger = logger

    def debug(self, msg: str, *args, **kwargs):
        """Log niveau DEBUG"""
        if self._logger:
            self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log niveau INFO"""
        if self._logger:
            self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log niveau WARNING"""
        if self._logger:
            self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log niveau ERROR"""
        if self._logger:
            self._logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log niveau CRITICAL"""
        if self._logger:
            self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """Log une exception avec traceback"""
        if self._logger:
            self._logger.exception(msg, *args, **kwargs)

    @property
    def is_active(self) -> bool:
        """Vérifie si le logger est actif"""
        return self._logger is not None


# ═══════════════════════════════════════════════════════════════
# HELPER POUR CONFIRMATIONS
# ═══════════════════════════════════════════════════════════════

def confirm_action(message: str, default: bool = False) -> bool:
    """
    Demande confirmation à l'utilisateur de manière standardisée

    Args:
        message: Message à afficher
        default: Valeur par défaut si l'utilisateur appuie juste sur Entrée

    Returns:
        True si l'utilisateur confirme, False sinon
    """
    default_str = "O/n" if default else "o/N"

    while True:
        try:
            response = input(f"{message} ({default_str}): ").strip().lower()

            if not response:
                return default

            if response in ['oui', 'o', 'yes', 'y']:
                return True
            elif response in ['non', 'n', 'no']:
                return False
            else:
                print("Réponse invalide. Tapez 'oui' ou 'non' (ou o/n)")
        except (EOFError, KeyboardInterrupt):
            print()  # Nouvelle ligne
            return False


# ═══════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    'create_success_result',
    'create_error_result',
    'handle_command_errors',
    'CommandResultHandler',
    'try_execute_builtin',
    'SafeLogger',
    'confirm_action',
]
