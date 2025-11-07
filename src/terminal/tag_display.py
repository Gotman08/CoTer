"""
Affichage Rich pour les balises structurées de la réponse IA.

Chaque type de balise a un style visuel spécifique pour faciliter
la lecture et identifier rapidement l'information importante.
"""

from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from rich import box

from src.terminal.rich_console import get_console


class TagDisplay:
    """Gestionnaire d'affichage Rich pour les balises IA"""

    # Configuration des styles pour chaque type de balise
    TAG_STYLES = {
        'Title Commande': {
            'color': 'cyan',
            'bold': True,
            'prefix': '▶',
            'box_style': 'cyan',
        },
        'Description': {
            'color': 'bright_white',
            'bold': False,
            'prefix': '│',
            'box_style': 'dim',
        },
        'Commande': {
            'color': 'green',
            'bold': True,
            'prefix': '›',
            'box_style': 'green',
            'use_panel': True,  # Afficher dans un panel
        },
        'no Commande': {
            'color': 'yellow',
            'bold': False,
            'prefix': '⚠',
            'box_style': 'yellow',
        },
        'DANGER': {
            'color': 'red',
            'bold': True,
            'prefix': '⚠',
            'box_style': 'red',
            'use_panel': True,
        },
        'Titre Code': {
            'color': 'magenta',
            'bold': True,
            'prefix': '▸',
            'box_style': 'magenta',
        },
        'Code': {
            'color': 'cyan',
            'bold': False,
            'prefix': None,
            'box_style': 'cyan',
            'use_panel': True,
            'syntax': True,  # Coloration syntaxique
        },
        'fichier': {
            'color': 'blue',
            'bold': False,
            'prefix': '📄',
            'box_style': 'blue',
        },
    }

    def __init__(self, console: Optional[Console] = None):
        """
        Initialise le gestionnaire d'affichage.

        Args:
            console: Console Rich à utiliser (ou get_console() par défaut)
        """
        self.console = console or get_console()

    def display_tag(self, tag_name: str, content: str):
        """
        Affiche une balise avec le style approprié.

        Args:
            tag_name: Nom de la balise (ex: "Title Commande", "Description")
            content: Contenu à afficher
        """
        if not content or not content.strip():
            return  # Ne rien afficher si vide

        # Récupérer le style de la balise
        style_config = self.TAG_STYLES.get(tag_name, {})

        # Cas spécial : panel pour commandes et code
        if style_config.get('use_panel'):
            self._display_panel(tag_name, content, style_config)
        else:
            self._display_simple(tag_name, content, style_config)

    def _display_simple(self, tag_name: str, content: str, style_config: Dict[str, Any]):
        """
        Affichage simple avec préfixe et couleur.

        Args:
            tag_name: Nom de la balise
            content: Contenu à afficher
            style_config: Configuration du style
        """
        # Créer le texte formaté
        text = Text()

        # Ajouter le préfixe si défini
        prefix = style_config.get('prefix')
        if prefix:
            text.append(f"{prefix} ", style=f"bold {style_config.get('color', 'white')}")

        # Ajouter le nom de la balise (optionnel pour certaines balises)
        if tag_name not in ['Description']:  # Description = pas de titre
            label_style = "bold" if style_config.get('bold') else ""
            text.append(f"{tag_name}\n", style=f"{label_style} {style_config.get('color', 'white')}")

        # Ajouter le contenu
        content_style = "bold" if style_config.get('bold') else ""
        content_color = style_config.get('color', 'white')

        # Indenter le contenu pour les sections avec préfixe
        if prefix and tag_name != 'Description':
            # Indenter chaque ligne
            indented_content = '\n'.join(f"  {line}" for line in content.split('\n'))
            text.append(indented_content, style=f"{content_style} {content_color}")
        else:
            text.append(content, style=f"{content_style} {content_color}")

        self.console.print(text)

    def _display_panel(self, tag_name: str, content: str, style_config: Dict[str, Any]):
        """
        Affichage dans un panel Rich.

        Args:
            tag_name: Nom de la balise
            content: Contenu à afficher
            style_config: Configuration du style
        """
        # Titre du panel
        prefix = style_config.get('prefix', '')
        title_text = f"{prefix} {tag_name}" if prefix else tag_name

        # Coloration syntaxique pour le code
        if style_config.get('syntax') and tag_name == 'Code':
            # Essayer de détecter le langage (par défaut: python)
            syntax = Syntax(content, "python", theme="monokai", line_numbers=False)
            panel_content = syntax
        else:
            # Texte simple
            panel_content = content.strip()

        # Créer le panel
        panel = Panel(
            panel_content,
            title=f"[bold]{title_text}[/bold]",
            border_style=style_config.get('box_style', 'white'),
            box=box.ROUNDED,
            padding=(0, 1),
        )

        self.console.print(panel)

    def display_section_start(self, tag_name: str):
        """
        Affiche le début d'une section (utile pour le streaming).

        Args:
            tag_name: Nom de la balise qui commence
        """
        style_config = self.TAG_STYLES.get(tag_name, {})
        color = style_config.get('color', 'white')
        prefix = style_config.get('prefix', '')

        # Afficher le header de section
        text = Text()
        if prefix:
            text.append(f"{prefix} ", style=f"bold {color}")
        text.append(tag_name, style=f"bold {color}")

        self.console.print()  # Ligne vide avant
        self.console.print(text)

    def display_content_stream(self, tag_name: str, token: str):
        """
        Affiche un token dans le contexte d'une balise (pour streaming).

        Args:
            tag_name: Nom de la balise active
            token: Token à afficher
        """
        style_config = self.TAG_STYLES.get(tag_name, {})
        color = style_config.get('color', 'white')

        # Pour les panels (commande/code), on accumule et affiche à la fin
        # Pour les autres, on affiche token par token
        if not style_config.get('use_panel'):
            self.console.print(token, end="", style=color)

    def display_section_end(self):
        """Affiche la fin d'une section."""
        self.console.print()  # Ligne vide après

    def display_separator(self):
        """Affiche un séparateur visuel entre sections."""
        self.console.print("─" * 60, style="dim")

    def display_raw(self, content: str):
        """
        Affiche du contenu brut (sans balise).
        Utilisé comme fallback si aucune balise détectée.

        Args:
            content: Contenu à afficher
        """
        self.console.print(content, style="bright_white")

    def get_tag_style(self, tag_name: str) -> Dict[str, Any]:
        """
        Récupère la configuration de style pour une balise.

        Args:
            tag_name: Nom de la balise

        Returns:
            Configuration du style
        """
        return self.TAG_STYLES.get(tag_name, {
            'color': 'white',
            'bold': False,
            'prefix': None,
            'box_style': 'white',
        })


# ═══════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = ['TagDisplay']
