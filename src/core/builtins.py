"""
Builtins - Commandes shell intégrées
Commandes natives du shell CoTer
"""

import os
import sys
from typing import Dict, Any, Callable, Optional
from pathlib import Path
import logging

from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from src.terminal.rich_console import get_console
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
            console = get_console()
            console.success("Historique effacé")
        elif args[0] == 'search' and len(args) > 1:
            query = ' '.join(args[1:])
            results = self.terminal.history_manager.search(query)
            console = get_console()

            if results:
                # Table de résultats
                table = Table(
                    title=f"Résultats de recherche pour '{query}'",
                    show_header=True,
                    box=box.SIMPLE,
                    border_style="info"
                )

                table.add_column("#", style="dim", width=4, justify="right")
                table.add_column("Commande", style="bright_white")

                for i, entry in enumerate(results[:10], 1):
                    table.add_row(str(i), entry['command'])

                console.print(table)
            else:
                console.print(f"[error]Aucun résultat pour '{query}'[/error]")

        elif args[0] == 'stats':
            stats = self.terminal.history_manager.get_statistics()
            console = get_console()

            # Table des statistiques
            stats_table = Table(
                title="Statistiques d'Historique",
                show_header=False,
                box=box.SIMPLE,
                border_style="cyan"
            )

            stats_table.add_column("Métrique", style="label")
            stats_table.add_column("Valeur", style="bright_white", justify="right")

            stats_table.add_row("Total de commandes", str(stats['total']))
            stats_table.add_row("Taux de succès", f"{stats['success_rate']:.1f}%")
            stats_table.add_section()

            for mode, count in stats['by_mode'].items():
                stats_table.add_row(f"Mode {mode}", str(count))

            console.print(stats_table)
        else:
            print(f"Usage: history [clear|search <terme>|stats]")

        return create_success_result('')

    def cmd_help(self, args: list) -> Dict[str, Any]:
        """Commande help - Afficher l'aide avec Rich"""
        console = get_console()

        # Table des modes
        modes_table = Table(
            title="Modes du Shell",
            show_header=True,
            box=box.SIMPLE,
            border_style="cyan"
        )
        modes_table.add_column("Commande", style="mode.auto", no_wrap=True)
        modes_table.add_column("Description", style="bright_white")

        modes_table.add_row("/manual", "Mode shell direct (sans IA)")
        modes_table.add_row("/auto", "Mode IA (langage naturel)")
        modes_table.add_row("/agent", "Mode projet autonome")
        modes_table.add_row("/status", "Statut du shell")

        # Table des builtins
        builtins_table = Table(
            title="Commandes Builtins",
            show_header=True,
            box=box.SIMPLE,
            border_style="cyan"
        )
        builtins_table.add_column("Commande", style="command", no_wrap=True)
        builtins_table.add_column("Description", style="bright_white")

        builtins_table.add_row("cd <dir>", "Changer de répertoire")
        builtins_table.add_row("pwd", "Afficher répertoire courant")
        builtins_table.add_row("clear/cls", "Effacer l'écran")
        builtins_table.add_row("history", "Historique des commandes")
        builtins_table.add_row("env", "Variables d'environnement")
        builtins_table.add_row("export", "Exporter variable")
        builtins_table.add_row("echo", "Afficher texte")
        builtins_table.add_row("exit/quit", "Quitter le shell")

        # Table des commandes slash
        slash_table = Table(
            title="Commandes Slash",
            show_header=True,
            box=box.SIMPLE,
            border_style="cyan"
        )
        slash_table.add_column("Commande", style="info", no_wrap=True)
        slash_table.add_column("Description", style="bright_white")

        slash_table.add_row("/help", "Afficher cette aide")
        slash_table.add_row("/quit", "Quitter le shell")
        slash_table.add_row("/clear", "Effacer historique IA")
        slash_table.add_row("/history", "Historique détaillé")
        slash_table.add_row("/models", "Changer modèle Ollama")
        slash_table.add_row("/info", "Informations système")
        slash_table.add_row("/cache", "Statistiques du cache")
        slash_table.add_row("/hardware", "Informations hardware")

        # Panel d'exemples
        examples = Text()
        examples.append("\nMODE MANUAL:\n", style="subtitle")
        examples.append("  Commandes shell directes (comme bash)\n", style="dim")
        examples.append("  Exemples: ls -la, grep 'test' file.txt\n\n", style="dim")

        examples.append("MODE AUTO:\n", style="subtitle")
        examples.append("  Demandes en langage naturel\n", style="dim")
        examples.append("  Exemples: 'liste les fichiers', 'montre les processus'\n\n", style="dim")

        examples.append("MODE AGENT:\n", style="subtitle")
        examples.append("  Projets complets autonomes\n", style="dim")
        examples.append("  Exemple: /agent crée-moi une API REST\n", style="dim")

        # Afficher tout
        console.print(Panel(
            Text("AIDE - COTER SHELL", style="bold bright_white", justify="center"),
            border_style="info",
            box=box.HEAVY
        ))
        console.print(modes_table)
        console.print(builtins_table)
        console.print(slash_table)
        console.print(Panel(examples, border_style="dim", box=box.ROUNDED))

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
