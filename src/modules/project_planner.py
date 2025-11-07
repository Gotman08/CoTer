"""Planificateur de projets pour l'agent autonome"""

import json
from typing import Dict, List, Optional
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from src.terminal.rich_console import get_console

class ProjectPlanner:
    """Analyse les demandes et génère des plans de projets"""

    def __init__(self, ollama_client, logger=None):
        """
        Initialise le planificateur

        Args:
            ollama_client: Client Ollama pour l'analyse
            logger: Logger pour les messages
        """
        self.ollama = ollama_client
        self.logger = logger
        self.current_plan = None

    def analyze_request(self, user_request: str) -> Dict:
        """
        Analyse une demande utilisateur et détermine si c'est un projet complexe

        Args:
            user_request: Demande de l'utilisateur

        Returns:
            Dict avec 'is_complex', 'project_type', 'description'
        """
        prompt = f"""Analyse cette demande utilisateur et détermine s'il s'agit d'une demande de création de projet complexe nécessitant plusieurs fichiers et actions.

Demande: "{user_request}"

Réponds UNIQUEMENT avec un JSON au format:
{{
    "is_complex": true/false,
    "project_type": "type du projet" (ex: "flask_api", "fastapi_rest", "django_web", "cli_tool", "data_analysis", "simple_command"),
    "description": "brève description de ce qui est demandé",
    "estimated_files": nombre estimé de fichiers à créer
}}

Exemples:
- "liste les fichiers" -> {{"is_complex": false, "project_type": "simple_command", ...}}
- "crée une API REST avec FastAPI" -> {{"is_complex": true, "project_type": "fastapi_rest", ...}}
- "fais-moi un bot Discord" -> {{"is_complex": true, "project_type": "discord_bot", ...}}
"""

        try:
            response = self.ollama.generate(prompt)

            # Parser la réponse JSON
            # Nettoyer la réponse pour extraire le JSON
            response = response.strip()
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]

            analysis = json.loads(response.strip())

            if self.logger:
                self.logger.info(f"Analyse de la demande: {analysis}")

            return analysis

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur lors de l'analyse: {e}")
            # Par défaut, considérer comme commande simple
            return {
                'is_complex': False,
                'project_type': 'simple_command',
                'description': user_request,
                'estimated_files': 0
            }

    def generate_project_plan(self, user_request: str, project_type: str) -> Dict:
        """
        Génère un plan détaillé pour créer un projet

        Args:
            user_request: Demande originale
            project_type: Type de projet identifié

        Returns:
            Dict avec le plan complet
        """
        prompt = f"""Tu es un expert en architecture logicielle. Génère un plan détaillé pour créer ce projet:

Demande: "{user_request}"
Type de projet: {project_type}

Génère un plan au format JSON avec cette structure:
{{
    "project_name": "nom du projet (slug format)",
    "description": "description courte",
    "structure": [
        {{"type": "dir", "path": "chemin/du/dossier"}},
        {{"type": "file", "path": "chemin/fichier.py", "description": "ce que fait ce fichier"}}
    ],
    "steps": [
        {{
            "step_number": 1,
            "action": "create_structure",
            "description": "Créer la structure de dossiers",
            "details": ["dossier1", "dossier2"]
        }},
        {{
            "step_number": 2,
            "action": "create_file",
            "description": "Générer main.py",
            "file_path": "main.py",
            "file_type": "python",
            "template": "flask_main" (si applicable)
        }}
    ],
    "dependencies": ["fastapi", "uvicorn", "pydantic"],
    "git_init": true,
    "estimated_time": "temps estimé en minutes"
}}

Actions possibles: create_structure, create_file, run_command, git_commit

Sois précis et complet. Liste TOUS les fichiers nécessaires (code, config, readme, etc.)
"""

        try:
            response = self.ollama.generate(prompt, system_prompt="Tu es un expert en architecture logicielle. Réponds UNIQUEMENT avec du JSON valide, sans texte supplémentaire.")

            # Nettoyer et parser
            response = response.strip()
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]

            plan = json.loads(response.strip())

            # Valider le plan
            plan = self._validate_and_enhance_plan(plan)

            self.current_plan = plan

            if self.logger:
                self.logger.info(f"Plan généré: {len(plan.get('steps', []))} étapes")

            return plan

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur lors de la génération du plan: {e}")

            # Plan par défaut basique
            return self._generate_fallback_plan(user_request, project_type)

    def _validate_and_enhance_plan(self, plan: Dict) -> Dict:
        """
        Valide et améliore un plan généré

        Args:
            plan: Plan brut généré par l'IA

        Returns:
            Plan validé et amélioré
        """
        # Assurer que les champs requis existent
        if 'project_name' not in plan:
            plan['project_name'] = 'mon_projet'

        if 'steps' not in plan:
            plan['steps'] = []

        if 'dependencies' not in plan:
            plan['dependencies'] = []

        if 'git_init' not in plan:
            plan['git_init'] = True

        # Ajouter étape finale de commit si git_init
        if plan['git_init']:
            has_git_commit = any(step.get('action') == 'git_commit' for step in plan['steps'])
            if not has_git_commit:
                plan['steps'].append({
                    'step_number': len(plan['steps']) + 1,
                    'action': 'git_commit',
                    'description': 'Commit initial du projet',
                    'message': f"Initial commit: {plan['description']}"
                })

        # Ajouter création de requirements.txt si dépendances
        if plan['dependencies']:
            has_requirements = any(
                step.get('file_path') == 'requirements.txt'
                for step in plan['steps']
                if step.get('action') == 'create_file'
            )
            if not has_requirements:
                plan['steps'].insert(len(plan['steps']) - 1, {
                    'step_number': len(plan['steps']),
                    'action': 'create_file',
                    'description': 'Créer requirements.txt',
                    'file_path': 'requirements.txt',
                    'file_type': 'text',
                    'content': '\n'.join(plan['dependencies'])
                })

        return plan

    def _generate_fallback_plan(self, user_request: str, project_type: str) -> Dict:
        """
        Génère un plan de secours si l'IA échoue

        Args:
            user_request: Demande utilisateur
            project_type: Type de projet

        Returns:
            Plan basique
        """
        project_name = user_request.lower().replace(' ', '_')[:30]

        return {
            'project_name': project_name,
            'description': user_request,
            'structure': [
                {'type': 'dir', 'path': project_name},
                {'type': 'dir', 'path': f'{project_name}/src'}
            ],
            'steps': [
                {
                    'step_number': 1,
                    'action': 'create_structure',
                    'description': 'Créer la structure de base',
                    'details': [project_name, f'{project_name}/src']
                },
                {
                    'step_number': 2,
                    'action': 'create_file',
                    'description': 'Créer fichier principal',
                    'file_path': f'{project_name}/main.py',
                    'file_type': 'python'
                },
                {
                    'step_number': 3,
                    'action': 'create_file',
                    'description': 'Créer README',
                    'file_path': f'{project_name}/README.md',
                    'file_type': 'markdown'
                }
            ],
            'dependencies': [],
            'git_init': True,
            'estimated_time': '5'
        }

    def display_plan(self, plan: Dict) -> str:
        """
        Formate un plan pour l'affichage avec Rich

        Args:
            plan: Plan à afficher

        Returns:
            String formaté pour affichage (sera print() par l'appelant)
        """
        console = get_console()

        # Informations du projet
        project_name = plan.get('project_name', 'N/A')
        description = plan.get('description', 'N/A')
        estimated_time = plan.get('estimated_time', 'N/A')

        # Panel d'informations projet
        info_text = Text()
        info_text.append("Projet: ", style="label")
        info_text.append(f"{project_name}\n", style="bold cyan")
        info_text.append("Description: ", style="label")
        info_text.append(f"{description}\n", style="bright_white")

        if estimated_time != 'N/A':
            info_text.append("Temps estimé: ", style="label")
            info_text.append(f"~{estimated_time} minutes", style="dim")

        info_panel = Panel(
            info_text,
            title="[bold]PLAN D'EXÉCUTION AUTONOME[/bold]",
            border_style="mode.agent",
            box=box.ROUNDED,
            padding=(1, 2)
        )

        # Table des étapes
        steps_table = Table(
            title="Étapes du Plan",
            show_header=True,
            box=box.SIMPLE,
            border_style="mode.agent"
        )

        steps_table.add_column("#", style="dim", width=4, justify="right")
        steps_table.add_column("Action", style="info", width=15)
        steps_table.add_column("Description", style="bright_white", no_wrap=False)

        # Icônes par type d'action (sans emojis, utiliser des symboles Rich)
        action_styles = {
            'create_structure': ("[dim]DIR[/dim]", "Créer structure"),
            'create_file': ("[dim]FILE[/dim]", "Créer fichier"),
            'run_command': ("[dim]CMD[/dim]", "Exécuter commande"),
            'git_commit': ("[dim]GIT[/dim]", "Commit Git")
        }

        for i, step in enumerate(plan.get('steps', []), 1):
            action = step.get('action', 'unknown')
            action_label, action_type = action_styles.get(action, ("[dim]ACT[/dim]", "Action"))
            description = step.get('description', 'N/A')

            steps_table.add_row(
                str(i),
                action_type,
                description
            )

        # Dépendances (si présentes)
        deps_text = ""
        if plan.get('dependencies'):
            deps_list = "\n".join([f"  • {dep}" for dep in plan['dependencies']])
            deps_text = f"\n\n[label]Dépendances à installer:[/label]\n{deps_list}"

        # Capture la sortie Rich en string pour retourner
        with console.console.capture() as capture:
            console.console.print(info_panel)
            console.console.print(steps_table)
            if deps_text:
                console.console.print(deps_text)

        return capture.get()

    def get_current_plan(self) -> Optional[Dict]:
        """Retourne le plan actuel"""
        return self.current_plan

    def clear_plan(self):
        """Efface le plan actuel"""
        self.current_plan = None
