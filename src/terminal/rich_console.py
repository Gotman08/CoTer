"""
Console Rich unifiée pour un affichage professionnel et sobre.
Remplace tous les print() et emojis par des composants Rich structurés.
"""

from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.status import Status
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.text import Text
from rich import box


# Thème cohérent et professionnel pour CoTer
COTER_THEME = Theme({
    # États
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "info": "bold cyan",

    # Éléments UI
    "prompt": "bold magenta",
    "command": "bold white",
    "output": "dim white",
    "path": "cyan",

    # Modes
    "mode.manual": "yellow",
    "mode.auto": "green",
    "mode.agent": "blue",

    # Sections
    "title": "bold bright_white",
    "subtitle": "bold cyan",
    "label": "dim cyan",

    # Bordures
    "border": "bright_black",
})


class RichConsoleManager:
    """
    Gestionnaire singleton de la console Rich.
    Centralise tous les affichages pour une cohérence visuelle.
    """

    _instance: Optional['RichConsoleManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.console = Console(theme=COTER_THEME, highlight=False)
        self._initialized = True

    # ═══════════════════════════════════════════════════════════════
    # MÉTHODES GÉNÉRIQUES
    # ═══════════════════════════════════════════════════════════════

    def print(self, *args, **kwargs):
        """Affichage générique via Rich Console."""
        self.console.print(*args, **kwargs)

    def print_panel(self, content: str, title: str = "", style: str = "border", **kwargs):
        """Affiche un panel Rich."""
        self.console.print(Panel(content, title=title, border_style=style, **kwargs))

    def clear(self):
        """Efface l'écran."""
        self.console.clear()

    # ═══════════════════════════════════════════════════════════════
    # MESSAGES D'ÉTAT
    # ═══════════════════════════════════════════════════════════════

    def success(self, message: str):
        """Message de succès."""
        self.console.print(f"[success]✓[/success] {message}")

    def error(self, message: str):
        """Message d'erreur."""
        self.console.print(f"[error]✗[/error] {message}")

    def warning(self, message: str):
        """Message d'avertissement."""
        self.console.print(f"[warning]![/warning] {message}")

    def info(self, message: str):
        """Message d'information."""
        self.console.print(f"[info]i[/info] {message}")

    # ═══════════════════════════════════════════════════════════════
    # BANNER & DÉMARRAGE
    # ═══════════════════════════════════════════════════════════════

    def print_banner(self, model: str, host: str, mode: str, mode_description: str):
        """
        Affiche le banner de démarrage sobre et professionnel.
        """
        # Titre principal
        title = Text()
        title.append("TERMINAL IA AUTONOME", style="bold bright_white")
        title.append(" • ", style="dim")
        title.append("CoTer", style="bold cyan")

        # Informations de configuration
        config_text = Text()
        config_text.append("Modèle: ", style="label")
        config_text.append(f"{model}\n", style="info")
        config_text.append("Host: ", style="label")
        config_text.append(f"{host}\n", style="dim")
        config_text.append("Mode: ", style="label")
        config_text.append(f"{mode}", style=f"mode.{mode.lower()}")
        config_text.append(f" - {mode_description}", style="dim")

        # Panel principal
        panel = Panel(
            config_text,
            title=title,
            border_style="cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        )

        self.console.print("\n")
        self.console.print(panel)

        # Commandes disponibles
        commands_text = Text()
        commands_text.append("Commandes: ", style="label")
        commands_text.append("/manual ", style="mode.manual")
        commands_text.append("/auto ", style="mode.auto")
        commands_text.append("/agent ", style="mode.agent")
        commands_text.append("/help /quit", style="dim")

        self.console.print(commands_text, justify="center")
        self.console.print()

    def print_hardware_report(self, report_data: Dict[str, Any]):
        """
        Affiche le rapport d'optimisation hardware dans un format sobre.
        """
        table = Table(
            title="Configuration Hardware",
            show_header=False,
            box=box.ROUNDED,
            border_style="cyan",
            padding=(0, 1)
        )

        table.add_column("Paramètre", style="label", no_wrap=True)
        table.add_column("Valeur", style="bright_white")

        # Extraction des données du rapport
        device = report_data.get('device', 'N/A')
        ram = report_data.get('ram', 'N/A')
        cpu = report_data.get('cpu', 'N/A')
        workers = report_data.get('workers', 'N/A')
        cache_size = report_data.get('cache_size', 'N/A')
        timeout = report_data.get('timeout', 'N/A')
        max_steps = report_data.get('max_steps', 'N/A')

        table.add_row("Device", device)
        table.add_row("RAM", ram)
        table.add_row("CPU", cpu)
        table.add_section()
        table.add_row("Workers", str(workers))
        table.add_row("Cache", cache_size)
        table.add_row("Timeout", timeout)
        table.add_row("Max Steps", str(max_steps))

        self.console.print(table)

    # ═══════════════════════════════════════════════════════════════
    # PROMPT & INTERACTION
    # ═══════════════════════════════════════════════════════════════

    def get_prompt_text(self, current_dir: str, mode: str) -> Text:
        """
        Génère le prompt utilisateur stylisé.
        """
        prompt = Text()

        # Indicateur de mode
        mode_styles = {
            "MANUAL": ("⌨", "mode.manual"),
            "AUTO": ("◉", "mode.auto"),
            "AGENT": ("●", "mode.agent")
        }

        symbol, style = mode_styles.get(mode.upper(), ("○", "dim"))
        prompt.append(f"{symbol} ", style=style)

        # Répertoire courant
        prompt.append("[", style="dim")
        prompt.append(current_dir, style="path")
        prompt.append("]", style="dim")
        prompt.append("\n> ", style="prompt")

        return prompt

    def input(self, prompt_text: Text) -> str:
        """
        Demande une saisie utilisateur avec un prompt Rich.
        """
        self.console.print()
        self.console.print(prompt_text, end="")
        return input()

    # ═══════════════════════════════════════════════════════════════
    # RÉSULTATS DE COMMANDES
    # ═══════════════════════════════════════════════════════════════

    def print_command_result(self, result: Dict[str, Any]):
        """
        Affiche le résultat d'une commande de manière structurée.
        """
        success = result.get('success', False)
        output = result.get('output', '')
        error = result.get('error', '')

        if success:
            self.success("Commande exécutée avec succès")

            if output:
                # Affiche la sortie dans un panel
                self.console.print()
                output_panel = Panel(
                    output.strip(),
                    title="[label]Sortie[/label]",
                    border_style="success",
                    box=box.ROUNDED,
                    padding=(1, 2)
                )
                self.console.print(output_panel)
        else:
            self.error("Échec de la commande")

            if error:
                error_panel = Panel(
                    error.strip(),
                    title="[label]Erreur[/label]",
                    border_style="error",
                    box=box.ROUNDED,
                    padding=(1, 2)
                )
                self.console.print(error_panel)

    # ═══════════════════════════════════════════════════════════════
    # AGENT MODE
    # ═══════════════════════════════════════════════════════════════

    def print_agent_step(self, step_number: int, total_steps: int, description: str):
        """
        Affiche une étape de l'agent de manière sobre.
        """
        progress_text = Text()
        progress_text.append(f"[{step_number}/{total_steps}] ", style="label")
        progress_text.append(description, style="bright_white")

        self.console.print(progress_text)

    def create_agent_progress(self) -> Progress:
        """
        Crée une barre de progression pour le mode agent.
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )

    def create_status(self, message: str) -> Status:
        """
        Crée un spinner de status.
        """
        return Status(message, console=self.console)

    # ═══════════════════════════════════════════════════════════════
    # TABLES & STATS
    # ═══════════════════════════════════════════════════════════════

    def print_stats_table(self, stats: Dict[str, Any]):
        """
        Affiche les statistiques dans une table formatée.
        """
        table = Table(
            title="Statistiques",
            show_header=True,
            box=box.SIMPLE,
            border_style="cyan"
        )

        table.add_column("Catégorie", style="label")
        table.add_column("Valeur", style="bright_white", justify="right")

        for key, value in stats.items():
            table.add_row(key, str(value))

        self.console.print(table)

    def print_models_table(self, models: List[Dict[str, Any]]):
        """
        Affiche la liste des modèles disponibles.
        """
        table = Table(
            title="Modèles Ollama Disponibles",
            show_header=True,
            box=box.ROUNDED,
            border_style="cyan"
        )

        table.add_column("#", style="dim", width=3)
        table.add_column("Nom", style="info")
        table.add_column("Taille", style="label", justify="right")

        for idx, model in enumerate(models, 1):
            name = model.get('name', 'N/A')
            size = model.get('size', 'N/A')
            table.add_row(str(idx), name, size)

        self.console.print(table)

    def print_history_table(self, history: List[Dict[str, Any]], limit: int = 20):
        """
        Affiche l'historique des commandes.
        """
        table = Table(
            title=f"Historique (dernières {limit} commandes)",
            show_header=True,
            box=box.SIMPLE,
            border_style="cyan"
        )

        table.add_column("#", style="dim", width=5)
        table.add_column("Commande", style="command")
        table.add_column("Statut", style="label", width=10)

        for idx, entry in enumerate(history[-limit:], 1):
            cmd = entry.get('command', 'N/A')
            success = entry.get('success', False)
            status_text = "[success]✓[/success]" if success else "[error]✗[/error]"

            table.add_row(str(idx), cmd, status_text)

        self.console.print(table)

    # ═══════════════════════════════════════════════════════════════
    # HELP & DOCUMENTATION
    # ═══════════════════════════════════════════════════════════════

    def print_help(self, help_text: str):
        """
        Affiche l'aide formatée en Markdown.
        """
        md = Markdown(help_text)
        self.console.print(md)

    def print_code(self, code: str, language: str = "python"):
        """
        Affiche du code avec coloration syntaxique.
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)


# Instance globale singleton
_console_manager: Optional[RichConsoleManager] = None


def get_console() -> RichConsoleManager:
    """
    Récupère l'instance singleton du gestionnaire de console.
    """
    global _console_manager
    if _console_manager is None:
        _console_manager = RichConsoleManager()
    return _console_manager
