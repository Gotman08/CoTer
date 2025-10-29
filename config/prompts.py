"""Prompts système pour l'interaction avec Ollama"""

SYSTEM_PROMPT_MAIN = """Tu es un assistant IA autonome intégré dans un terminal Linux.
Tu dois aider l'utilisateur à exécuter des commandes shell sur son système.

RÈGLES IMPORTANTES:
1. Quand l'utilisateur te demande de faire quelque chose, tu dois générer UNIQUEMENT la commande shell correspondante
2. Ne fournis AUCUNE explication, AUCUN texte supplémentaire, juste la commande
3. Si la commande est dangereuse ou destructive, préfixe ta réponse par [DANGER]
4. Si la demande n'est pas une action système exécutable, préfixe par [NO_COMMAND] et explique brièvement
5. Privilégie toujours les commandes sûres et non destructives
6. Tu connais parfaitement bash, les commandes Linux, les outils système du Raspberry Pi

EXEMPLES:
User: "liste les fichiers du dossier actuel"
Assistant: ls -la

User: "montre l'utilisation du disque"
Assistant: df -h

User: "supprime tous les fichiers"
Assistant: [DANGER] rm -rf *

User: "quelle est la capitale de la France?"
Assistant: [NO_COMMAND] Je suis un assistant terminal. Pour des questions générales, utilise une autre interface. Je suis spécialisé dans les commandes système.

Tu es sur un Raspberry Pi 5 sous Linux. Adapte tes commandes en conséquence.
"""

SYSTEM_PROMPT_CONVERSATIONAL = """Tu es un assistant IA autonome pour terminal Linux.
L'utilisateur vient de te poser une question ou de faire une remarque qui n'est PAS une demande d'action système.

Tu peux avoir une conversation normale avec l'utilisateur, mais rappelle-lui que tu es spécialisé dans l'exécution de commandes système.

Sois concis, utile et professionnel.
Si la conversation dérive trop, suggère poliment de revenir aux commandes système.
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

HELP_TEXT = """
╔════════════════════════════════════════════════════════════════╗
║           TERMINAL IA AUTONOME - AIDE                          ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  UTILISATION:                                                  ║
║  - Tapez votre demande en langage naturel                      ║
║  - L'IA va générer et exécuter la commande appropriée          ║
║                                                                ║
║  COMMANDES SPÉCIALES:                                          ║
║  /help      - Affiche cette aide                               ║
║  /clear     - Efface l'historique de conversation              ║
║  /history   - Affiche l'historique des commandes               ║
║  /models    - Liste les modèles Ollama disponibles             ║
║  /info      - Affiche les informations système                 ║
║  /templates - Liste les templates de projets                   ║
║  /agent     - Active le mode agent autonome                    ║
║  /pause     - Met en pause l'agent autonome                    ║
║  /resume    - Reprend l'agent autonome                         ║
║  /stop      - Arrête l'agent autonome                          ║
║  /cache     - Affiche les stats du cache (/cache clear = vider)║
║  /hardware  - Affiche les infos hardware et optimisations      ║
║  /rollback  - Gère les snapshots (/rollback list|restore|stats)║
║  /security  - Affiche le rapport de sécurité des commandes     ║
║  /corrections - Stats auto-correction (/corrections stats|last)║
║  /quit      - Quitte le terminal IA                            ║
║                                                                ║
║  EXEMPLES DE DEMANDES SIMPLES:                                 ║
║  • "liste les fichiers du dossier actuel"                      ║
║  • "montre-moi l'espace disque disponible"                     ║
║  • "affiche les processus en cours"                            ║
║  • "crée un dossier nommé test"                                ║
║                                                                ║
║  MODE AGENT AUTONOME (Projets Complexes):                      ║
║  • "crée-moi une API REST avec FastAPI"                        ║
║  • "fais-moi un bot Discord"                                   ║
║  • "génère un projet Flask avec authentification"              ║
║  L'agent planifiera et exécutera toutes les étapes!            ║
║                                                                ║
║  SÉCURITÉ:                                                     ║
║  • Les commandes dangereuses nécessitent une confirmation      ║
║  • Certaines commandes sont bloquées pour votre sécurité       ║
║  • Tous les logs sont enregistrés dans ./logs/                 ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
"""

ASCII_LOGO = """
 ╔══════════════════════════════════════════════════════════════╗
 ║                                                              ║
 ║   ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗  ║
 ║   ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗ ║
 ║      ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║ ║
 ║      ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║ ║
 ║      ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║ ║
 ║      ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ║
 ║                                                              ║
 ║                🤖  Terminal IA Autonome  🤖                  ║
 ║                     Propulsé par Ollama                      ║
 ║                                                              ║
 ╚══════════════════════════════════════════════════════════════╝
"""

GOODBYE_MESSAGE = """
╔════════════════════════════════════════╗
║                                        ║
║     Merci d'avoir utilisé             ║
║     Terminal IA Autonome              ║
║                                        ║
║     À bientôt! 👋                     ║
║                                        ║
╚════════════════════════════════════════╝
"""

# Messages pour le mode agent autonome

AGENT_MODE_BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║             🤖  MODE AGENT AUTONOME ACTIVÉ  🤖               ║
║                                                               ║
║  L'IA va analyser votre demande, créer un plan d'action      ║
║  et l'exécuter étape par étape automatiquement.              ║
║                                                               ║
║  Vous pourrez valider le plan avant l'exécution.             ║
║  Appuyez sur Ctrl+C pour arrêter à tout moment.              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""

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
    Formate l'affichage de progression d'une étape

    Args:
        current: Numéro de l'étape actuelle
        total: Nombre total d'étapes
        description: Description de l'étape

    Returns:
        String formaté
    """
    progress_bar_length = 40
    progress = int((current / total) * progress_bar_length)
    bar = "█" * progress + "░" * (progress_bar_length - progress)
    percentage = int((current / total) * 100)

    return f"""
┌─────────────────────────────────────────────────────────────┐
│ Progression: [{bar}] {percentage}%      │
│ Étape {current}/{total}: {description[:45]:<45} │
└─────────────────────────────────────────────────────────────┘
"""
