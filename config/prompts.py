"""Prompts système pour l'interaction avec Ollama"""

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn
from rich import box
from src.terminal.rich_console import get_console

SYSTEM_PROMPT_MAIN = """Tu es un assistant IA autonome intégré dans un terminal Linux.
Tu dois aider l'utilisateur à exécuter des commandes shell sur son système.

MODE ITÉRATIF:
Tu travailles par ÉTAPES. Après chaque commande exécutée, tu verras le résultat.
Génère la PROCHAINE commande logique basée sur les résultats précédents et le contexte complet.

Si tu as trouvé la réponse ou complété la tâche, indique clairement dans ta description:
"✓ Tâche terminée : [résumé de ce qui a été trouvé/fait]"

Si tu ne peux pas continuer ou n'as pas de solution:
"✗ Impossible de continuer : [explication]"

RÈGLES IMPORTANTES:
1. Quand l'utilisateur te demande de faire quelque chose, analyse sa demande et génère la commande shell appropriée
2. Tu peux utiliser des BALISES pour structurer ta réponse et montrer ton raisonnement (RECOMMANDÉ)
3. Si la commande est dangereuse ou destructive, utilise OBLIGATOIREMENT la balise [DANGER]
4. Si la demande n'est pas une action système exécutable, utilise OBLIGATOIREMENT [no Commande]
5. Privilégie toujours les commandes sûres et non destructives
6. Tu connais parfaitement bash, les commandes Linux, les outils système du Raspberry Pi

BALISES DISPONIBLES (optionnelles mais recommandées):
• [Title Commande] - Titre court décrivant l'action à effectuer
• [Description] - Explication de ta démarche et de ce que tu vas faire
• [Commande] - La commande shell finale à exécuter
• [no Commande] - OBLIGATOIRE si ce n'est pas une action système
• [DANGER] - OBLIGATOIRE pour les commandes dangereuses/destructives
• [Titre Code] - Titre pour un bloc de code (scripts, fichiers)
• [Code] - Bloc de code (script Python, config, etc.)
• [fichier] - Chemin d'un fichier concerné

EXEMPLES AVEC BALISES (format recommandé):
User: "liste les fichiers du dossier actuel"
Assistant: [Title Commande] Liste des fichiers
[Description] Je vais lister tous les fichiers du répertoire courant avec les détails (permissions, taille, date)
[Commande] ls -la

User: "montre l'utilisation du disque"
Assistant: [Title Commande] Espace disque disponible
[Description] Affichage de l'utilisation des partitions en format lisible
[Commande] df -h

User: "supprime tous les fichiers"
Assistant: [Title Commande] ⚠️  SUPPRESSION TOTALE
[Description] Cette commande est TRÈS DANGEREUSE! Elle supprimera TOUS les fichiers du répertoire courant de manière irréversible.
[DANGER] rm -rf *

User: "quelle est la capitale de la France?"
Assistant: [Title Commande] Question non-système
[no Commande] Je suis un assistant terminal spécialisé dans les commandes système. Pour des questions générales, utilise une autre interface.

EXEMPLES SANS BALISES (format minimal, aussi accepté):
User: "liste les fichiers"
Assistant: ls -la

User: "quelle est la capitale de la France?"
Assistant: [no Commande] Je suis un assistant terminal. Pour des questions générales, utilise une autre interface.

COMPATIBILITÉ: Tu peux répondre avec ou sans balises. Les balises permettent un meilleur affichage visuel et montrent ton raisonnement, mais ne sont pas obligatoires (sauf [DANGER] et [no Commande] quand requis).

Tu es sur un Raspberry Pi 5 sous Linux. Adapte tes commandes en conséquence.
"""

SYSTEM_PROMPT_CONVERSATIONAL = """Tu es un assistant IA autonome pour terminal Linux.
L'utilisateur vient de te poser une question ou de faire une remarque qui n'est PAS une demande d'action système.

Tu peux avoir une conversation normale avec l'utilisateur, mais rappelle-lui que tu es spécialisé dans l'exécution de commandes système.

Sois concis, utile et professionnel.
Si la conversation dérive trop, suggère poliment de revenir aux commandes système.
"""

SYSTEM_PROMPT_FAST = """Tu es un expert shell Linux ultra-efficace.
Génère UNE SEULE commande optimale et complète qui répond parfaitement à la demande.

MODE ONE-SHOT:
Tu dois tout faire en une seule commande. Pas d'étapes multiples, pas de suivi.
Utilise des pipes, redirections, et combinaisons pour tout accomplir d'un coup.

RÈGLES STRICTES:
1. UNE SEULE commande finale (pipes et && autorisés)
2. Maximum d'efficacité - tout faire en un coup
3. Gestion des erreurs intégrée (2>/dev/null si approprié)
4. Privilégie les commandes sûres et non destructives
5. Utilise OBLIGATOIREMENT [DANGER] si destructif
6. Utilise OBLIGATOIREMENT [no Commande] si pas une action système

BALISES OBLIGATOIRES:
• [Title Commande] - Titre court de l'action
• [Description] - Explication brève et précise
• [Commande] - La commande shell optimale

EXEMPLES:
User: "trouve tous les fichiers Python modifiés aujourd'hui"
Assistant: [Title Commande] Recherche fichiers Python récents
[Description] Recherche tous les .py modifiés dans les dernières 24h
[Commande] find . -name "*.py" -type f -mtime -1 2>/dev/null | sort

User: "combien de lignes de code dans mon projet"
Assistant: [Title Commande] Comptage lignes de code
[Description] Compte toutes les lignes dans les fichiers source du projet
[Commande] find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.java" \) -exec wc -l {} + | tail -n 1

Tu es sur un Raspberry Pi 5 sous Linux. Adapte tes commandes en conséquence.
"""

COMMAND_EXPLANATION_PROMPT = """Explique brièvement ce que fait la commande suivante en une ou deux phrases courtes:

Commande: {command}

Fournis une explication simple et claire pour un utilisateur non-technique.
"""

ERROR_ANALYSIS_PROMPT = """La commande suivante a échoué:

Commande: {command}
Erreur: {error}

Analyse l'erreur et suggère:
1. Une explication simple du problème
2. Une commande corrigée si possible
3. Des alternatives si la commande n'est pas réalisable

Sois concis et pratique.
"""

def get_help_text() -> str:
    """
    Génère le texte d'aide avec Rich Panel.

    Returns:
        String formaté avec Rich
    """
    console = get_console()

    # Table des commandes
    commands_table = Table(
        show_header=True,
        box=box.SIMPLE,
        border_style="info",
        padding=(0, 1)
    )

    commands_table.add_column("Commande", style="info", no_wrap=True)
    commands_table.add_column("Description", style="bright_white")

    # Commandes de base
    commands_table.add_row("/help", "Affiche cette aide")
    commands_table.add_row("/clear", "Efface l'historique de conversation")
    commands_table.add_row("/history", "Affiche l'historique des commandes")
    commands_table.add_row("/models", "Liste les modèles Ollama disponibles")
    commands_table.add_row("/info", "Affiche les informations système")
    commands_table.add_row("/templates", "Liste les templates de projets")
    commands_table.add_section()

    # Mode agent
    commands_table.add_row("/agent", "Active le mode agent autonome")
    commands_table.add_row("/pause", "Met en pause l'agent autonome")
    commands_table.add_row("/resume", "Reprend l'agent autonome")
    commands_table.add_row("/stop", "Arrête l'agent autonome")
    commands_table.add_section()

    # Utilitaires
    commands_table.add_row("/cache", "Stats du cache (/cache clear)")
    commands_table.add_row("/hardware", "Infos hardware et optimisations")
    commands_table.add_row("/rollback", "Gère snapshots (list|restore|stats)")
    commands_table.add_row("/security", "Rapport de sécurité")
    commands_table.add_row("/corrections", "Stats auto-correction (stats|last)")
    commands_table.add_row("/quit", "Quitte le terminal IA")

    # Panel avec sections d'information
    info_text = Text()
    info_text.append("\nUTILISATION:\n", style="subtitle")
    info_text.append("  • Tapez votre demande en langage naturel\n", style="bright_white")
    info_text.append("  • L'IA va générer et exécuter la commande appropriée\n\n", style="bright_white")

    info_text.append("EXEMPLES DE DEMANDES SIMPLES:\n", style="subtitle")
    info_text.append("  • liste les fichiers du dossier actuel\n", style="dim")
    info_text.append("  • montre-moi l'espace disque disponible\n", style="dim")
    info_text.append("  • affiche les processus en cours\n", style="dim")
    info_text.append("  • crée un dossier nommé test\n\n", style="dim")

    info_text.append("MODE AGENT AUTONOME (Projets Complexes):\n", style="subtitle")
    info_text.append("  • crée-moi une API REST avec FastAPI\n", style="mode.agent")
    info_text.append("  • fais-moi un bot Discord\n", style="mode.agent")
    info_text.append("  • génère un projet Flask avec authentification\n", style="mode.agent")
    info_text.append("  L'agent planifiera et exécutera toutes les étapes!\n\n", style="dim")

    info_text.append("SÉCURITÉ:\n", style="subtitle")
    info_text.append("  • Les commandes dangereuses nécessitent confirmation\n", style="warning")
    info_text.append("  • Certaines commandes sont bloquées\n", style="warning")
    info_text.append("  • Logs enregistrés dans ./logs/\n", style="dim")

    # Capture la sortie Rich
    with console.console.capture() as capture:
        console.console.print(Panel(
            info_text,
            title="[bold]TERMINAL IA AUTONOME - AIDE[/bold]",
            border_style="info",
            box=box.ROUNDED,
            padding=(1, 2)
        ))
        console.console.print(commands_table)

    return capture.get()

# Backward compatibility: Garde la constante pour ne pas casser le code existant
HELP_TEXT = get_help_text()

def get_ascii_logo() -> str:
    """
    Génère le logo de bienvenue avec Rich Panel.

    Returns:
        String formaté avec Rich
    """
    console = get_console()

    # Titre stylisé
    title_text = Text("TERMINAL IA AUTONOME\nCoTer\n\nPropulsé par Ollama + Rich Library",
                      justify="center")
    # Style les différentes parties
    title_text.stylize("bold bright_white", 0, 20)  # "TERMINAL IA AUTONOME"
    title_text.stylize("bold cyan", 21, 26)  # "CoTer"
    title_text.stylize("dim italic", 28)

    # Panel
    with console.console.capture() as capture:
        console.console.print(Panel(
            title_text,
            border_style="cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        ))

    return capture.get()

# Backward compatibility
ASCII_LOGO = get_ascii_logo()

def get_goodbye_message() -> str:
    """
    Génère le message d'au revoir avec Rich Panel.

    Returns:
        String formaté avec Rich
    """
    console = get_console()

    content = Text("Merci d'avoir utilisé\nTerminal IA Autonome\n\nÀ bientôt!", justify="center")
    content.stylize("bright_white", 0, 22)  # "Merci d'avoir utilisé"
    content.stylize("bold cyan", 23, 45)  # "Terminal IA Autonome"
    content.stylize("dim", 47)

    with console.console.capture() as capture:
        console.console.print(Panel(
            content,
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2)
        ))

    return capture.get()

# Backward compatibility
GOODBYE_MESSAGE = get_goodbye_message()

# Messages pour le mode agent autonome

def get_agent_mode_banner() -> str:
    """
    Génère le banner du mode agent avec Rich Panel.

    Returns:
        String formaté avec Rich
    """
    console = get_console()

    content = Text()
    content.append("MODE AGENT AUTONOME ACTIVÉ\n\n", style="bold mode.agent")
    content.append("L'IA va analyser votre demande, créer un plan d'action\n", style="bright_white")
    content.append("et l'exécuter étape par étape automatiquement.\n\n", style="bright_white")
    content.append("Vous pourrez valider le plan avant l'exécution.\n", style="dim")
    content.append("Appuyez sur Ctrl+C pour arrêter à tout moment.", style="dim")

    with console.console.capture() as capture:
        console.console.print(Panel(
            content,
            border_style="mode.agent",
            box=box.HEAVY,
            padding=(1, 2)
        ))

    return capture.get()

# Backward compatibility
AGENT_MODE_BANNER = get_agent_mode_banner()

AGENT_ANALYZING = """
🔍 Analyse de votre demande en cours...
   L'IA détermine s'il s'agit d'un projet complexe nécessitant
   plusieurs actions automatisées.
"""

AGENT_PLANNING = """
📋 Génération du plan d'exécution...
   L'IA crée un plan détaillé avec toutes les étapes nécessaires.
"""

AGENT_EXECUTING = """
🚀 Lancement de l'exécution autonome...
   L'IA va maintenant exécuter chaque étape du plan.

   [Ctrl+C pour arrêter | Entrée pour continuer]
"""

AGENT_PAUSED = """
⏸️  Agent en pause
   L'exécution est temporairement suspendue.
   Tapez /resume pour reprendre ou /stop pour arrêter.
"""

AGENT_STOPPED = """
🛑 Agent arrêté
   L'exécution a été arrêtée par l'utilisateur.
"""

AGENT_COMPLETED = """
✅ Exécution terminée avec succès!
   Toutes les étapes du plan ont été exécutées.
"""

AGENT_ERROR = """
❌ Erreur lors de l'exécution
   Une erreur s'est produite pendant l'exécution du plan.
"""

def format_step_progress(current: int, total: int, description: str) -> str:
    """
    Formate l'affichage de progression d'une étape avec Rich

    Args:
        current: Numéro de l'étape actuelle
        total: Nombre total d'étapes
        description: Description de l'étape

    Returns:
        String formaté avec Rich
    """
    console = get_console()

    # Calcul pourcentage
    percentage = int((current / total) * 100)

    # Panel de progression
    content = Text()
    content.append(f"Progression: {percentage}%\n", style="label")
    content.append(f"Étape {current}/{total}: ", style="dim")
    content.append(description[:60], style="bright_white")

    with console.console.capture() as capture:
        console.console.print(Panel(
            content,
            border_style="mode.agent",
            box=box.SIMPLE,
            padding=(0, 1)
        ))

    return capture.get()
