"""
Terminal Interface - Interface utilisateur du shell CoTer

Ce module contient l'interface terminal divisée en composants modulaires:
- shell_interface: Boucle principale et orchestration
- command_router: Routing des commandes spéciales (/)
- mode_handlers: Gestion des 3 modes (MANUAL/AUTO/AGENT)
- display_manager: Affichage et statistiques
"""

# Pour l'instant, rétrocompatibilité avec l'ancien TerminalInterface
# TODO: Une fois la migration terminée, exporter ShellInterface
# from .shell_interface import ShellInterface
# __all__ = ['ShellInterface']

__all__ = []
