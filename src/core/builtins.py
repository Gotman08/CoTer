"""
Builtins - Commandes shell intégrées
Commandes natives du shell CoTer
"""

import os
import sys
from typing import Dict, Any, Callable, Optional
from pathlib import Path
import logging

from src.utils.command_helpers import create_success_result, create_error_result

logger = logging.getLogger(__name__)


class BuiltinCommands:
    """
    Gestionnaire de commandes builtins (intégrées au shell)

    Commandes implémentées:
    - cd: Changer de répertoire
    - pwd: Afficher le répertoire courant
    - exit/quit: Quitter le shell
    - clear: Effacer l'écran
    - history: Afficher l'historique
    - help: Afficher l'aide
    - env: Afficher/modifier les variables d'environnement
    - export: Exporter une variable d'environnement
    """

    def __init__(self, terminal_interface):
        """
        Initialise les commandes builtins

        Args:
            terminal_interface: Référence à l'interface terminal
        """
        self.terminal = terminal_interface
        self.current_dir = os.getcwd()

        # Mapping des commandes builtins vers leurs handlers
        self.commands: Dict[str, Callable] = {
            'cd': self.cmd_cd,
            'pwd': self.cmd_pwd,
            'exit': self.cmd_exit,
            'quit': self.cmd_exit,
            'clear': self.cmd_clear,
            'cls': self.cmd_clear,  # Alias Windows
            'history': self.cmd_history,
            'help': self.cmd_help,
            'env': self.cmd_env,
            'export': self.cmd_export,
            'echo': self.cmd_echo,
        }

    def is_builtin(self, command: str) -> bool:
        """
        Vérifie si une commande est builtin

        Args:
            command: La commande à vérifier

        Returns:
            True si c'est une commande builtin
        """
        cmd_name = command.split()[0] if command else ""
        return cmd_name in self.commands

    def execute(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Exécute une commande builtin

        Args:
            command: La commande à exécuter

        Returns:
            Résultat de l'exécution ou None si pas builtin
        """
        if not command or not command.strip():
            return None

        parts = command.split()
        cmd_name = parts[0]

        if cmd_name not in self.commands:
            return None

        try:
            return self.commands[cmd_name](parts[1:])
        except Exception as e:
            logger.error(f"Erreur dans commande builtin {cmd_name}: {e}")
            return create_error_result(f"Erreur: {str(e)}", 1)

    def cmd_cd(self, args: list) -> Dict[str, Any]:
        """Commande cd - Changer de répertoire"""
        if not args:
            # cd sans argument = aller au home
            target_dir = str(Path.home())
        else:
            target_dir = args[0]

        # Expander ~
        target_dir = os.path.expanduser(target_dir)

        # Chemins relatifs
        if not os.path.isabs(target_dir):
            target_dir = os.path.join(self.current_dir, target_dir)

        target_dir = os.path.normpath(target_dir)

        if os.path.isdir(target_dir):
            self.current_dir = target_dir
            os.chdir(target_dir)  # Changer aussi le cwd du process Python

            # Mettre à jour le executor si disponible
            if hasattr(self.terminal, 'executor'):
                self.terminal.executor.current_directory = target_dir

            return create_success_result('')  # cd ne produit pas de sortie normalement
        else:
            return create_error_result(f"cd: {target_dir}: No such file or directory", 1)

    def cmd_pwd(self, args: list) -> Dict[str, Any]:
        """Commande pwd - Afficher le répertoire courant"""
        return create_success_result(self.current_dir)

    def cmd_exit(self, args: list) -> Dict[str, Any]:
        """Commande exit/quit - Quitter le shell"""
        print("\n👋 Au revoir !")
        logger.info("Shell fermé via commande exit")

        # Déterminer le code de sortie
        exit_code = 0
        if args:
            try:
                exit_code = int(args[0])
            except ValueError:
                exit_code = 0

        sys.exit(exit_code)

    def cmd_clear(self, args: list) -> Dict[str, Any]:
        """Commande clear/cls - Effacer l'écran"""
        # Effacer l'écran selon l'OS
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/macOS
            os.system('clear')

        return create_success_result('')

    def cmd_history(self, args: list) -> Dict[str, Any]:
        """Commande history - Afficher/gérer l'historique"""
        if not hasattr(self.terminal, 'history_manager'):
            return create_error_result("Historique non disponible", 1)

        # Sous-commandes
        if not args:
            # Afficher l'historique via la méthode du terminal
            self.terminal._show_history()
        elif args[0] == 'clear':
            self.terminal.history_manager.clear()
            print("✅ Historique effacé")
        elif args[0] == 'search' and len(args) > 1:
            query = ' '.join(args[1:])
            results = self.terminal.history_manager.search(query)
            if results:
                print(f"\n🔍 Résultats de recherche pour '{query}':")
                print("─" * 60)
                for i, entry in enumerate(results[:10], 1):
                    print(f"{i}. {entry['command']}")
                print("─" * 60)
            else:
                print(f"❌ Aucun résultat pour '{query}'")
        elif args[0] == 'stats':
            stats = self.terminal.history_manager.get_statistics()
            print("\n📊 Statistiques d'historique:")
            print("─" * 60)
            print(f"Total de commandes: {stats['total']}")
            print(f"Taux de succès: {stats['success_rate']:.1f}%")
            print(f"\nPar mode:")
            for mode, count in stats['by_mode'].items():
                print(f"  • {mode}: {count}")
            print("─" * 60)
        else:
            print(f"Usage: history [clear|search <terme>|stats]")

        return create_success_result('')

    def cmd_help(self, args: list) -> Dict[str, Any]:
        """Commande help - Afficher l'aide"""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║           AIDE - COTER SHELL (Terminal IA Autonome)          ║
╠══════════════════════════════════════════════════════════════╣
║ MODES DU SHELL:                                              ║
║   /manual     - Mode shell direct (exécution sans IA)        ║
║   /auto       - Mode IA activé (langage naturel via Ollama)  ║
║   /agent      - Mode projet autonome (multi-étapes)          ║
║   /status     - Afficher le statut du shell                  ║
╠══════════════════════════════════════════════════════════════╣
║ COMMANDES BUILTINS:                                          ║
║   cd <dir>    - Changer de répertoire                        ║
║   pwd         - Afficher le répertoire courant               ║
║   clear/cls   - Effacer l'écran                              ║
║   history     - Afficher l'historique des commandes          ║
║   env         - Afficher les variables d'environnement       ║
║   export      - Exporter une variable d'environnement        ║
║   echo        - Afficher un texte                            ║
║   exit/quit   - Quitter le shell                             ║
╠══════════════════════════════════════════════════════════════╣
║ COMMANDES SLASH (/):                                         ║
║   /help       - Afficher cette aide                          ║
║   /quit       - Quitter le shell                             ║
║   /clear      - Effacer l'historique IA                      ║
║   /history    - Afficher l'historique détaillé               ║
║   /models     - Changer de modèle Ollama                     ║
║   /info       - Informations système                         ║
║   /cache      - Statistiques du cache                        ║
║   /hardware   - Informations hardware                        ║
╚══════════════════════════════════════════════════════════════╝

EN MODE MANUAL:
  Vous tapez directement des commandes shell (comme bash).
  Exemples: ls -la, grep "test" file.txt, ps aux | grep python

EN MODE AUTO:
  Vous tapez des demandes en langage naturel.
  Exemples: "liste les fichiers", "montre les processus python"

EN MODE AGENT:
  Pour créer des projets complets de manière autonome.
  Exemple: /agent crée-moi une API REST avec FastAPI
"""
        print(help_text)
        return create_success_result('')

    def cmd_env(self, args: list) -> Dict[str, Any]:
        """Commande env - Afficher les variables d'environnement"""
        if not args:
            # Afficher toutes les variables
            output_lines = []
            for key, value in sorted(os.environ.items()):
                output_lines.append(f"{key}={value}")

            return create_success_result('\n'.join(output_lines))
        else:
            # Afficher une variable spécifique
            var_name = args[0]
            value = os.environ.get(var_name)

            if value is not None:
                return create_success_result(f"{var_name}={value}")
            else:
                return create_error_result(f"env: {var_name}: Variable not set", 1)

    def cmd_export(self, args: list) -> Dict[str, Any]:
        """Commande export - Exporter une variable d'environnement"""
        if not args:
            return create_error_result("Usage: export VAR=value", 1)

        assignment = ' '.join(args)

        if '=' not in assignment:
            return create_error_result("Usage: export VAR=value", 1)

        var_name, var_value = assignment.split('=', 1)
        var_name = var_name.strip()
        var_value = var_value.strip().strip('"').strip("'")

        os.environ[var_name] = var_value

        return create_success_result('')

    def cmd_echo(self, args: list) -> Dict[str, Any]:
        """Commande echo - Afficher un texte"""
        output = ' '.join(args)

        # Supporter les variables d'environnement ($VAR)
        import re
        def replace_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, '')

        output = re.sub(r'\$(\w+)', replace_var, output)

        return create_success_result(output)

    def get_builtin_names(self) -> list:
        """Retourne la liste des noms de commandes builtins"""
        return list(self.commands.keys())

    def __repr__(self) -> str:
        return f"BuiltinCommands({len(self.commands)} commands)"
