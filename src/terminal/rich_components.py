"""
Composants Rich réutilisables pour Terminal IA.
Factory methods pour créer des panels, tables et autres éléments visuels.
"""

from typing import Dict, Any, List, Optional
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box


# ═══════════════════════════════════════════════════════════════
# PANELS
# ═══════════════════════════════════════════════════════════════

def create_result_panel(
    output: str,
    title: str = "Sortie",
    success: bool = True
) -> Panel:
    """
    Crée un panel pour afficher le résultat d'une commande.

    Args:
        output: Contenu de la sortie
        title: Titre du panel
        success: True pour bordure verte, False pour rouge

    Returns:
        Panel Rich formaté
    """
    border_style = "success" if success else "error"

    return Panel(
        output.strip(),
        title=f"[label]{title}[/label]",
        border_style=border_style,
        box=box.ROUNDED,
        padding=(1, 2)
    )


def create_info_panel(
    content: str,
    title: str = "",
    style: str = "info"
) -> Panel:
    """
    Crée un panel d'information générique.

    Args:
        content: Contenu du panel
        title: Titre optionnel
        style: Style de la bordure (info, warning, error, success)

    Returns:
        Panel Rich formaté
    """
    return Panel(
        content.strip(),
        title=f"[bold]{title}[/bold]" if title else "",
        border_style=style,
        box=box.ROUNDED,
        padding=(1, 2)
    )


def create_warning_panel(message: str) -> Panel:
    """
    Crée un panel d'avertissement.
    """
    return Panel(
        message,
        title="[bold]Avertissement[/bold]",
        border_style="warning",
        box=box.HEAVY,
        padding=(1, 2)
    )


def create_error_panel(error_message: str, title: str = "Erreur") -> Panel:
    """
    Crée un panel d'erreur.
    """
    return Panel(
        error_message.strip(),
        title=f"[bold]{title}[/bold]",
        border_style="error",
        box=box.HEAVY,
        padding=(1, 2)
    )


# ═══════════════════════════════════════════════════════════════
# TABLES
# ═══════════════════════════════════════════════════════════════

def create_hardware_table(hardware_info: Dict[str, Any]) -> Table:
    """
    Crée une table pour afficher les informations hardware.

    Args:
        hardware_info: Dictionnaire avec device, ram, cpu, workers, etc.

    Returns:
        Table Rich formatée
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

    # Informations système
    if 'device' in hardware_info:
        table.add_row("Device", hardware_info['device'])
    if 'ram' in hardware_info:
        table.add_row("RAM", hardware_info['ram'])
    if 'cpu' in hardware_info:
        table.add_row("CPU", hardware_info['cpu'])

    # Séparation
    if any(k in hardware_info for k in ['workers', 'cache_size', 'timeout', 'max_steps']):
        table.add_section()

    # Optimisations
    if 'workers' in hardware_info:
        table.add_row("Workers", str(hardware_info['workers']))
    if 'cache_size' in hardware_info:
        table.add_row("Cache", hardware_info['cache_size'])
    if 'timeout' in hardware_info:
        table.add_row("Timeout", hardware_info['timeout'])
    if 'max_steps' in hardware_info:
        table.add_row("Max Steps", str(hardware_info['max_steps']))

    return table


def create_models_table(models: List[Dict[str, Any]], current_model: Optional[str] = None) -> Table:
    """
    Crée une table listant les modèles Ollama disponibles.

    Args:
        models: Liste de dictionnaires avec 'name' et 'size'
        current_model: Nom du modèle actuellement sélectionné

    Returns:
        Table Rich formatée
    """
    table = Table(
        title="Modèles Ollama Disponibles",
        show_header=True,
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1)
    )

    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Nom", style="info")
    table.add_column("Taille", style="label", justify="right")
    table.add_column("Statut", style="dim", width=10)

    for idx, model in enumerate(models, 1):
        name = model.get('name', 'N/A')
        size = model.get('size', 'N/A')

        # Marque le modèle actuel
        status = "[success]●[/success] Actif" if name == current_model else ""

        table.add_row(str(idx), name, size, status)

    return table


def create_history_table(
    history: List[Dict[str, Any]],
    limit: int = 20,
    show_timestamps: bool = False
) -> Table:
    """
    Crée une table avec l'historique des commandes.

    Args:
        history: Liste de dictionnaires avec 'command', 'success', 'timestamp'
        limit: Nombre maximum de commandes à afficher
        show_timestamps: Afficher les timestamps

    Returns:
        Table Rich formatée
    """
    table = Table(
        title=f"Historique des Commandes (dernières {min(limit, len(history))})",
        show_header=True,
        box=box.SIMPLE,
        border_style="cyan"
    )

    table.add_column("#", style="dim", width=5, justify="right")
    table.add_column("Commande", style="command", no_wrap=False)
    table.add_column("Statut", style="label", width=8, justify="center")

    if show_timestamps:
        table.add_column("Date", style="dim", width=19)

    # Prend les N dernières commandes
    recent_history = history[-limit:] if len(history) > limit else history

    for idx, entry in enumerate(recent_history, 1):
        cmd = entry.get('command', 'N/A')
        success = entry.get('success', False)
        timestamp = entry.get('timestamp', '')

        # Symbole de statut
        status_symbol = "[success]✓[/success]" if success else "[error]✗[/error]"

        if show_timestamps:
            table.add_row(str(idx), cmd, status_symbol, timestamp)
        else:
            table.add_row(str(idx), cmd, status_symbol)

    return table


def create_stats_table(stats: Dict[str, Any], title: str = "Statistiques") -> Table:
    """
    Crée une table générique pour afficher des statistiques.

    Args:
        stats: Dictionnaire clé-valeur
        title: Titre de la table

    Returns:
        Table Rich formatée
    """
    table = Table(
        title=title,
        show_header=False,
        box=box.SIMPLE,
        border_style="cyan",
        padding=(0, 1)
    )

    table.add_column("Métrique", style="label", no_wrap=True)
    table.add_column("Valeur", style="bright_white", justify="right")

    for key, value in stats.items():
        # Formate les valeurs selon leur type
        if isinstance(value, bool):
            display_value = "[success]Oui[/success]" if value else "[dim]Non[/dim]"
        elif isinstance(value, (int, float)):
            display_value = f"{value:,}"
        else:
            display_value = str(value)

        table.add_row(key, display_value)

    return table


def create_cache_stats_table(cache_stats: Dict[str, Any]) -> Table:
    """
    Crée une table spécifique pour les statistiques de cache.

    Args:
        cache_stats: Statistiques du cache (hits, misses, size, etc.)

    Returns:
        Table Rich formatée
    """
    table = Table(
        title="Statistiques du Cache",
        show_header=True,
        box=box.ROUNDED,
        border_style="cyan"
    )

    table.add_column("Métrique", style="label")
    table.add_column("Valeur", style="bright_white", justify="right")
    table.add_column("Info", style="dim")

    # Hits et misses
    hits = cache_stats.get('hits', 0)
    misses = cache_stats.get('misses', 0)
    total = hits + misses
    hit_rate = (hits / total * 100) if total > 0 else 0

    table.add_row("Hits", f"{hits:,}", "[success]Requêtes en cache[/success]")
    table.add_row("Misses", f"{misses:,}", "[dim]Requêtes non cachées[/dim]")
    table.add_row("Taux de hit", f"{hit_rate:.1f}%", "[info]Efficacité[/info]")

    table.add_section()

    # Taille et capacité
    if 'size' in cache_stats:
        table.add_row("Entrées", f"{cache_stats['size']:,}", "Nombre d'éléments")
    if 'max_size' in cache_stats:
        table.add_row("Capacité", f"{cache_stats['max_size']:,}", "Maximum")

    return table


def create_agent_plan_table(steps: List[Dict[str, Any]]) -> Table:
    """
    Crée une table pour afficher le plan de l'agent.

    Args:
        steps: Liste des étapes du plan avec 'action', 'description', 'status'

    Returns:
        Table Rich formatée
    """
    table = Table(
        title="Plan d'Exécution Agent",
        show_header=True,
        box=box.ROUNDED,
        border_style="mode.agent"
    )

    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Action", style="info", width=15)
    table.add_column("Description", style="bright_white", no_wrap=False)
    table.add_column("Statut", style="label", width=10, justify="center")

    status_icons = {
        'pending': "[dim]○[/dim]",
        'in_progress': "[info]◐[/info]",
        'completed': "[success]●[/success]",
        'failed': "[error]✗[/error]"
    }

    for idx, step in enumerate(steps, 1):
        action = step.get('action', 'N/A')
        description = step.get('description', '')
        status = step.get('status', 'pending')

        status_icon = status_icons.get(status, "[dim]?[/dim]")

        table.add_row(str(idx), action, description, status_icon)

    return table


# ═══════════════════════════════════════════════════════════════
# TEXTES FORMATÉS
# ═══════════════════════════════════════════════════════════════

def create_mode_indicator(mode: str) -> Text:
    """
    Crée un indicateur de mode stylisé.

    Args:
        mode: Mode actuel (MANUAL, AUTO, AGENT)

    Returns:
        Text Rich avec symbole et couleur
    """
    mode_configs = {
        "MANUAL": ("⌨", "mode.manual", "Mode Manuel"),
        "AUTO": ("◉", "mode.auto", "Mode Automatique"),
        "AGENT": ("●", "mode.agent", "Mode Agent")
    }

    symbol, style, label = mode_configs.get(mode.upper(), ("○", "dim", mode))

    text = Text()
    text.append(symbol + " ", style=style)
    text.append(label, style=style)

    return text


def create_prompt_indicator(current_dir: str, mode: str) -> Text:
    """
    Crée l'indicateur de prompt.

    Args:
        current_dir: Répertoire courant
        mode: Mode actuel

    Returns:
        Text Rich pour le prompt
    """
    mode_symbols = {
        "MANUAL": ("⌨", "mode.manual"),
        "AUTO": ("◉", "mode.auto"),
        "AGENT": ("●", "mode.agent")
    }

    symbol, style = mode_symbols.get(mode.upper(), ("○", "dim"))

    prompt = Text()
    prompt.append(f"{symbol} ", style=style)
    prompt.append("[", style="dim")
    prompt.append(current_dir, style="path")
    prompt.append("]", style="dim")
    prompt.append("\n> ", style="prompt")

    return prompt


def create_status_text(success: bool, message: str) -> Text:
    """
    Crée un texte de statut avec icône.

    Args:
        success: True pour succès, False pour échec
        message: Message à afficher

    Returns:
        Text Rich formaté
    """
    text = Text()

    if success:
        text.append("✓ ", style="success")
        text.append(message, style="bright_white")
    else:
        text.append("✗ ", style="error")
        text.append(message, style="error")

    return text


# ═══════════════════════════════════════════════════════════════
# BANNERS ET MESSAGES SPÉCIAUX
# ═══════════════════════════════════════════════════════════════

def create_welcome_banner(model: str, host: str, version: str = "1.0") -> Panel:
    """
    Crée le banner de bienvenue CoTer.

    Args:
        model: Nom du modèle Ollama
        host: URL de l'host Ollama
        version: Version de CoTer

    Returns:
        Panel Rich formaté
    """
    # Titre principal
    title = Text()
    title.append("TERMINAL IA AUTONOME", style="bold bright_white")
    title.append(" • ", style="dim")
    title.append("CoTer", style="bold cyan")
    title.append(f" v{version}", style="dim")

    # Contenu
    content = Text()
    content.append("Modèle: ", style="label")
    content.append(f"{model}\n", style="info")
    content.append("Host: ", style="label")
    content.append(f"{host}\n", style="dim")
    content.append("\nPowered by Ollama + Rich Library", style="dim italic")

    return Panel(
        content,
        title=title,
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 2)
    )


def create_goodbye_panel() -> Panel:
    """
    Crée le panel de message d'au revoir.

    Returns:
        Panel Rich formaté
    """
    content = Text("Merci d'avoir utilisé\nTerminal IA Autonome", justify="center")
    content.stylize("bright_white", 0, 22)  # "Merci d'avoir utilisé"
    content.stylize("bold cyan", 23)

    return Panel(
        content,
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2)
    )


def create_help_panel(help_sections: Dict[str, List[str]]) -> Panel:
    """
    Crée un panel d'aide structuré.

    Args:
        help_sections: Dictionnaire {titre_section: [liste_commandes]}

    Returns:
        Panel Rich formaté
    """
    from rich.columns import Columns

    content_parts = []

    for section_title, commands in help_sections.items():
        # Titre de section
        section_text = Text()
        section_text.append(f"\n{section_title}\n", style="subtitle")

        content_parts.append(section_text)

        # Commandes de la section
        for cmd in commands:
            cmd_text = Text()
            cmd_text.append(f"  {cmd}\n", style="dim")
            content_parts.append(cmd_text)

    # Combiner tout le contenu
    full_content = Text()
    for part in content_parts:
        full_content.append(part)

    return Panel(
        full_content,
        title="[bold]AIDE - TERMINAL IA AUTONOME[/bold]",
        border_style="info",
        box=box.ROUNDED,
        padding=(1, 2)
    )


def create_agent_mode_banner() -> Panel:
    """
    Crée le banner d'activation du mode agent.

    Returns:
        Panel Rich formaté
    """
    content = Text()
    content.append("MODE AGENT AUTONOME ACTIVÉ\n\n", style="bold mode.agent")
    content.append("L'IA peut maintenant créer des projets complets de manière autonome.\n", style="bright_white")
    content.append("Décrivez votre projet et l'agent s'occupera du reste.\n\n", style="bright_white")
    content.append("Tapez '/manual' ou '/auto' pour revenir aux autres modes.", style="dim")

    return Panel(
        content,
        border_style="mode.agent",
        box=box.HEAVY,
        padding=(1, 2)
    )
