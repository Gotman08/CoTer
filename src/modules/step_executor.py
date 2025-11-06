"""
Step Executor - Exécution des étapes individuelles du plan

Ce module contient toute la logique d'exécution des actions:
- create_structure: Création de dossiers
- create_file: Création de fichiers avec code généré
- run_command: Exécution de commandes avec retry automatique
- git_commit: Commits Git
"""

import os
from typing import Dict
from .code_editor import CodeEditor
from .git_manager import GitManager
from ..utils.auto_corrector import AutoCorrector
from config import constants


class StepExecutor:
    """Exécute les étapes individuelles d'un plan de projet"""

    def __init__(self, executor, code_editor: CodeEditor, git_manager: GitManager,
                 auto_corrector: AutoCorrector, logger=None):
        """
        Initialise l'exécuteur d'étapes

        Args:
            executor: CommandExecutor pour l'exécution de commandes
            code_editor: CodeEditor pour la génération de code
            git_manager: GitManager pour les opérations Git
            auto_corrector: AutoCorrector pour le retry automatique
            logger: Logger optionnel
        """
        self.executor = executor
        self.code_editor = code_editor
        self.git_manager = git_manager
        self.auto_corrector = auto_corrector
        self.logger = logger

    def execute_step(self, step: Dict, project_path: str, context: Dict) -> Dict:
        """
        Exécute une étape du plan

        Args:
            step: Définition de l'étape
            project_path: Chemin du projet
            context: Contexte du projet

        Returns:
            Résultat de l'étape
        """
        action = step.get('action')

        try:
            if action == 'create_structure':
                return self.create_structure(step, project_path)

            elif action == 'create_file':
                return self.create_file(step, project_path, context)

            elif action == 'run_command':
                return self.run_command(step, project_path)

            elif action == 'git_commit':
                return self.git_commit(step, project_path)

            else:
                return {
                    'success': False,
                    'error': f'Action inconnue: {action}',
                    'can_continue': True
                }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur étape {action}: {e}")
            return {
                'success': False,
                'error': str(e),
                'can_continue': False
            }

    def create_structure(self, step: Dict, project_path: str) -> Dict:
        """
        Crée la structure de dossiers

        Args:
            step: Définition de l'étape
            project_path: Chemin du projet

        Returns:
            Résultat de la création
        """
        details = step.get('details', [])

        # Créer le dossier projet principal
        os.makedirs(project_path, exist_ok=True)

        created = [project_path]

        # Créer les sous-dossiers
        for detail in details:
            if isinstance(detail, str):
                folder_path = os.path.join(project_path, detail)
                os.makedirs(folder_path, exist_ok=True)
                created.append(folder_path)

        return {
            'success': True,
            'created': created,
            'count': len(created)
        }

    def create_file(self, step: Dict, project_path: str, context: Dict) -> Dict:
        """
        Crée un fichier avec du code généré

        Args:
            step: Définition de l'étape
            project_path: Chemin du projet
            context: Contexte du projet

        Returns:
            Résultat de la création
        """
        file_path = step.get('file_path', '')
        description = step.get('description', '')

        # Chemin complet
        if not file_path.startswith(project_path):
            full_path = os.path.join(project_path, file_path)
        else:
            full_path = file_path

        # Si le contenu est déjà fourni (ex: requirements.txt)
        if 'content' in step:
            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(step['content'])

                return {
                    'success': True,
                    'file_path': full_path,
                    'lines_written': len(step['content'].split('\n'))
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'can_continue': True
                }

        # Sinon, générer via code_editor
        return self.code_editor.create_file(full_path, description, context)

    def run_command(self, step: Dict, project_path: str) -> Dict:
        """
        Exécute une commande avec retry automatique

        Args:
            step: Définition de l'étape
            project_path: Chemin du projet

        Returns:
            Résultat de l'exécution
        """
        command = step.get('command', '')

        if not command:
            return {
                'success': False,
                'error': 'Commande vide',
                'can_continue': True
            }

        # Sauvegarder le répertoire courant
        original_cwd = self.executor.current_directory

        # Changer vers le projet
        self.executor.current_directory = project_path

        # Phase 3: Retry automatique avec auto-correction
        max_retries = constants.MAX_RETRY_ATTEMPTS
        attempt = 0
        current_command = command
        retry_history = []

        while attempt < max_retries:
            attempt += 1

            if self.logger and attempt > 1:
                self.logger.info(f"Tentative {attempt}/{max_retries} pour: {current_command}")

            # Exécuter la commande
            result = self.executor.execute(current_command)

            # Si succès, retourner immédiatement
            if result['success']:
                # Restaurer le répertoire
                self.executor.current_directory = original_cwd

                return {
                    'success': True,
                    'output': result.get('output', ''),
                    'error': '',
                    'can_continue': True,
                    'attempts': attempt,
                    'retry_history': retry_history
                }

            # Échec - analyser l'erreur
            error_output = result.get('error', '') or result.get('output', '')
            exit_code = result.get('exit_code', 1)

            if self.logger:
                self.logger.warning(f"Commande échouée (tentative {attempt}): {error_output[:200]}")

            # Analyser avec l'auto-correcteur
            analysis = self.auto_corrector.analyze_error(
                current_command,
                error_output,
                exit_code
            )

            # Ajouter à l'historique
            retry_history.append({
                'attempt': attempt,
                'command': current_command,
                'error': error_output[:500],
                'error_type': analysis.get('error_type'),
                'confidence': analysis.get('confidence')
            })

            # Si on peut corriger automatiquement, réessayer
            if analysis.get('can_retry') and attempt < max_retries:
                auto_fix = analysis.get('auto_fix')

                if self.logger:
                    self.logger.info(f"Auto-correction proposée: {auto_fix} (confiance: {analysis.get('confidence')})")

                # Utiliser la commande corrigée
                current_command = auto_fix

            else:
                # Plus de retry possible
                break

        # Restaurer le répertoire
        self.executor.current_directory = original_cwd

        # Toutes les tentatives ont échoué
        return {
            'success': False,
            'output': result.get('output', ''),
            'error': result.get('error', ''),
            'can_continue': True,
            'attempts': attempt,
            'retry_history': retry_history,
            'last_analysis': analysis
        }

    def git_commit(self, step: Dict, project_path: str) -> Dict:
        """
        Crée un commit Git

        Args:
            step: Définition de l'étape
            project_path: Chemin du projet

        Returns:
            Résultat du commit
        """
        # Initialiser git si nécessaire
        if not self.git_manager.is_git_repo(project_path):
            init_result = self.git_manager.init_repository(project_path)
            if not init_result['success']:
                return {
                    'success': False,
                    'error': f'Impossible d\'initialiser Git: {init_result.get("error")}',
                    'can_continue': True  # Git n'est pas critique
                }

        # Créer le commit
        message = step.get('message', None)
        commit_result = self.git_manager.commit(project_path, message)

        return {
            'success': commit_result['success'],
            'message': commit_result.get('message', ''),
            'error': commit_result.get('error', ''),
            'can_continue': True  # Git n'est pas critique
        }

    def serialize_step_for_worker(self, step: Dict, project_path: str, context: Dict) -> Dict:
        """
        Sérialise une étape pour l'exécution par un worker multiprocessing

        Args:
            step: Étape à sérialiser
            project_path: Chemin du projet
            context: Contexte du projet

        Returns:
            Dict sérialisable (sans objets complexes)
        """
        action = step.get('action')

        # Créer un dict sérialisable selon le type d'action
        if action == 'create_file':
            return {
                'action': 'create_file',
                'file_path': os.path.join(project_path, step.get('file_path', '')),
                'content': step.get('content', ''),
                'description': step.get('description', '')
            }

        elif action == 'run_command':
            return {
                'action': 'run_command',
                'command': step.get('command', ''),
                'cwd': project_path,
                'timeout': 120
            }

        elif action == 'create_structure':
            return {
                'action': 'create_structure',
                'base_path': project_path,
                'folders': step.get('details', [])
            }

        elif action == 'git_commit':
            # Git commit ne peut pas être parallélisé facilement, on le garde séquentiel
            return {
                'action': 'git_commit',
                'message': step.get('message', 'Auto commit'),
                'project_path': project_path
            }

        else:
            return {
                'action': action,
                'step_data': step
            }
