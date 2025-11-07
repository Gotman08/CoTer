"""
Prompt Manager - Gestion du prompt personnalisable
Génère et personnalise le prompt du shell selon le mode, le contexte, etc.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
import getpass
import platform

from rich.panel import Panel
from rich.text import Text
from rich import box
from src.terminal.rich_console import get_console


class PromptManager:
    """
    Gestionnaire de prompt personnalisable

    Fonctionnalités:
    - Prompt dynamique selon le mode (MANUAL/AUTO/AGENT)
    - Affichage du répertoire courant
    - Informations contextuelles (user, host, git branch, etc.)
    - Personnalisation via templates
    - Support des couleurs ANSI
    """

    # Codes couleur ANSI
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'dim': '\033[2m',
        'underline': '\033[4m',

        # Couleurs standard
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',

        # Couleurs vives
        'bright_black': '\033[90m',
        'bright_red': '\033[91m',
        'bright_green': '\033[92m',
        'bright_yellow': '\033[93m',
        'bright_blue': '\033[94m',
        'bright_magenta': '\033[95m',
        'bright_cyan': '\033[96m',
        'bright_white': '\033[97m',
    }

    def __init__(self, enable_colors: bool = True):
        """
        Initialise le gestionnaire de prompt

        Args:
            enable_colors: Activer les couleurs ANSI
        """
        self.enable_colors = enable_colors and self._supports_colors()
        self.username = getpass.getuser()
        self.hostname = platform.node()

    def _supports_colors(self) -> bool:
        """Vérifie si le terminal supporte les couleurs ANSI"""
        # Sur Windows, vérifier si c'est Windows Terminal ou un terminal moderne
        if os.name == 'nt':
            # Windows 10+ avec ANSI support
            return os.environ.get('WT_SESSION') is not None or \
                   os.environ.get('TERM_PROGRAM') is not None
        # Unix/Linux/macOS supportent généralement les couleurs
        return True

    def colorize(self, text: str, color: str) -> str:
        """
        Applique une couleur à un texte

        Args:
            text: Le texte à coloriser
            color: Nom de la couleur

        Returns:
            Texte colorisé si les couleurs sont activées
        """
        if not self.enable_colors:
            return text

        color_code = self.COLORS.get(color, '')
        reset_code = self.COLORS['reset']

        return f"{color_code}{text}{reset_code}"

    def get_short_path(self, path: str, max_length: int = 30) -> str:
        """
        Raccourcit un chemin pour l'affichage

        Args:
            path: Le chemin complet
            max_length: Longueur maximale

        Returns:
            Chemin raccourci
        """
        # Remplacer le home par ~
        home = str(Path.home())
        if path.startswith(home):
            path = "~" + path[len(home):]

        # Si trop long, afficher seulement le dernier dossier
        if len(path) > max_length:
            parts = Path(path).parts
            if len(parts) > 1:
                return f".../{parts[-1]}"

        return path

    def get_git_branch(self, directory: str) -> Optional[str]:
        """
        Détecte la branche Git courante

        Args:
            directory: Le répertoire à vérifier

        Returns:
            Nom de la branche Git ou None
        """
        try:
            git_dir = Path(directory)
            while git_dir != git_dir.parent:
                git_head = git_dir / '.git' / 'HEAD'
                if git_head.exists():
                    content = git_head.read_text().strip()
                    if content.startswith('ref: refs/heads/'):
                        return content.replace('ref: refs/heads/', '')
                    return 'detached'
                git_dir = git_dir.parent
        except:
            pass
        return None

    def generate_prompt(
        self,
        mode_symbol: str,
        current_dir: str,
        show_user: bool = False,
        show_host: bool = False,
        show_git: bool = True,
        multiline: bool = True
    ) -> str:
        """
        Génère le prompt complet

        Args:
            mode_symbol: Symbole du mode actuel (⌨️/🤖/🏗️)
            current_dir: Répertoire courant
            show_user: Afficher le nom d'utilisateur
            show_host: Afficher le hostname
            show_git: Afficher la branche Git
            multiline: Prompt sur plusieurs lignes

        Returns:
            Le prompt formaté
        """
        parts = []

        # Mode symbol (colorisé selon le mode)
        mode_colored = self._colorize_mode_symbol(mode_symbol)
        parts.append(mode_colored)

        # User@host
        if show_user or show_host:
            userhost = []
            if show_user:
                userhost.append(self.colorize(self.username, 'green'))
            if show_host:
                userhost.append(self.colorize(self.hostname, 'yellow'))

            if userhost:
                parts.append('@'.join(userhost))

        # Répertoire courant
        short_path = self.get_short_path(current_dir)
        path_colored = self.colorize(short_path, 'blue')
        parts.append(f"[{path_colored}]")

        # Branche Git (si disponible)
        if show_git:
            git_branch = self.get_git_branch(current_dir)
            if git_branch:
                git_colored = self.colorize(f"({git_branch})", 'magenta')
                parts.append(git_colored)

        # Assemblage
        if multiline:
            # Première ligne avec les infos
            line1 = ' '.join(parts)
            # Deuxième ligne avec le prompt
            prompt_char = self.colorize('>', 'bright_white')
            return f"\n{line1}\n{prompt_char} "
        else:
            # Tout sur une ligne
            prompt_char = self.colorize('>', 'bright_white')
            return f"\n{' '.join(parts)} {prompt_char} "

    def _colorize_mode_symbol(self, symbol: str) -> str:
        """
        Colorise le symbole de mode

        Args:
            symbol: Le symbole du mode

        Returns:
            Symbole colorisé
        """
        # Mapping symbole → couleur
        colors = {
            '⌨️': 'cyan',        # MANUAL
            '🤖': 'bright_green', # AUTO
            '🏗️': 'bright_yellow' # AGENT
        }

        # Si le symbole est un emoji, pas besoin de colorer
        # Sinon, appliquer la couleur correspondante
        for emoji, color in colors.items():
            if emoji in symbol:
                return symbol  # Les emojis sont déjà colorés

        # Fallback: colorer en blanc
        return self.colorize(symbol, 'bright_white')

    def generate_simple_prompt(self, mode_symbol: str, current_dir: str) -> str:
        """
        Génère un prompt simplifié (sans couleurs ni infos avancées)

        Args:
            mode_symbol: Symbole du mode
            current_dir: Répertoire courant

        Returns:
            Prompt simple
        """
        short_path = self.get_short_path(current_dir, max_length=40)
        return f"\n{mode_symbol} [{short_path}]\n> "

    def generate_minimal_prompt(self) -> str:
        """
        Génère un prompt minimal (juste le symbole >)

        Returns:
            Prompt minimal
        """
        return "> "

    def get_welcome_banner(self, mode: str, version: str = "1.0") -> str:
        """
        Génère une bannière de bienvenue

        Args:
            mode: Mode de démarrage
            version: Version de CoTer

        Returns:
            Bannière formatée
        """
        console = get_console()

        # Titre
        title = Text()
        title.append("CoTer", style="bold cyan")
        title.append(" - Terminal IA Autonome", style="bright_white")

        # Contenu
        content = Text()
        content.append(f"Version {version}\n", style="dim", justify="center")
        content.append(f"\nMode: ", style="label")
        content.append(f"{mode.upper()}\n", style=f"mode.{mode.lower()}")
        content.append("\nCommandes: ", style="label")
        content.append("/manual /auto /agent /help /quit", style="dim")

        # Capture Rich output
        with console.console.capture() as capture:
            console.console.print()  # Ligne vide avant
            console.console.print(Panel(
                content,
                title=title,
                border_style="cyan",
                box=box.ROUNDED,
                padding=(1, 2)
            ))
            console.console.print()  # Ligne vide après

        return capture.get()

    def format_error(self, message: str) -> str:
        """Formate un message d'erreur"""
        return self.colorize(f"✗ {message}", "red")

    def format_success(self, message: str) -> str:
        """Formate un message de succès"""
        return self.colorize(f"✓ {message}", "green")

    def format_warning(self, message: str) -> str:
        """Formate un avertissement"""
        return self.colorize(f"! {message}", "yellow")

    def format_info(self, message: str) -> str:
        """Formate une information"""
        return self.colorize(f"i {message}", "blue")

    def get_prompt_config(self) -> Dict[str, Any]:
        """
        Retourne la configuration actuelle du prompt

        Returns:
            Configuration sous forme de dictionnaire
        """
        return {
            'enable_colors': self.enable_colors,
            'username': self.username,
            'hostname': self.hostname,
            'supports_colors': self._supports_colors()
        }

    def __repr__(self) -> str:
        return f"PromptManager(colors={self.enable_colors}, user={self.username})"
