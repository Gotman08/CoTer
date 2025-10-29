"""Agent autonome pour exécuter des tâches complexes automatiquement"""

import time
import os
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta

from .project_planner import ProjectPlanner
from .code_editor import CodeEditor
from .git_manager import GitManager
from .command_executor import CommandExecutor
from ..utils.parallel_executor import ParallelExecutor
from ..utils.rollback_manager import RollbackManager
from ..utils.auto_corrector import AutoCorrector
from ..utils import parallel_workers
from config import constants

class AutonomousAgent:
    """Agent autonome qui planifie et exécute des tâches complexes"""

    def __init__(self, ollama_client, executor, settings, logger=None):
        """
        Initialise l'agent autonome

        Args:
            ollama_client: Client Ollama
            executor: Exécuteur de commandes
            settings: Configuration
            logger: Logger
        """
        self.ollama = ollama_client
        self.executor = executor
        self.settings = settings
        self.logger = logger

        # Initialiser les modules
        self.planner = ProjectPlanner(ollama_client, logger)
        self.code_editor = CodeEditor(ollama_client, logger)
        self.git_manager = GitManager(ollama_client, logger)

        # Initialiser l'exécuteur parallèle (Phase 1: Performance)
        self.parallel_executor = ParallelExecutor(logger=logger)
        if self.logger:
            self.logger.info(f"Exécution parallèle activée avec {self.parallel_executor.max_workers} workers")

        # Initialiser le gestionnaire de rollback (Phase 2: Sécurité)
        self.rollback_manager = RollbackManager(logger=logger)
        if self.logger:
            self.logger.info("Gestionnaire de rollback initialisé")

        # Initialiser l'auto-correcteur (Phase 3: Auto-correction)
        self.auto_corrector = AutoCorrector(ollama_client=ollama_client, logger=logger)
        if self.logger:
            self.logger.info("Auto-correcteur initialisé")

        # État de l'agent
        self.is_running = False
        self.is_paused = False
        self.current_plan = None
        self.current_step = 0
        self.start_time = None
        self.max_steps = constants.MAX_AGENT_STEPS
        self.max_duration = timedelta(minutes=constants.MAX_AGENT_DURATION_MINUTES)

        # Callbacks pour l'interface
        self.on_step_start = None
        self.on_step_complete = None
        self.on_pause = None
        self.on_error = None

    def execute_autonomous_task(self, user_request: str, callback: Optional[Callable] = None) -> Dict:
        """
        Exécute une tâche autonome complète

        Args:
            user_request: Demande utilisateur
            callback: Fonction callback pour les mises à jour

        Returns:
            Dict avec résultat final
        """
        try:
            self.is_running = True
            self.start_time = datetime.now()

            if self.logger:
                self.logger.info(f"Démarrage tâche autonome: {user_request}")

            # Phase 1: Analyse de la demande
            if callback:
                callback("analyse", "Analyse de votre demande...")

            analysis = self.planner.analyze_request(user_request)

            if not analysis.get('is_complex'):
                # Demande simple, pas besoin du mode autonome
                return {
                    'success': False,
                    'reason': 'not_complex',
                    'message': 'Cette demande ne nécessite pas le mode autonome',
                    'analysis': analysis
                }

            # Phase 2: Génération du plan
            if callback:
                callback("planning", "Génération du plan d'exécution...")

            plan = self.planner.generate_project_plan(
                user_request,
                analysis.get('project_type', 'unknown')
            )

            self.current_plan = plan

            # Vérifier la limite de steps
            if len(plan.get('steps', [])) > self.max_steps:
                return {
                    'success': False,
                    'reason': 'too_many_steps',
                    'message': f'Le plan dépasse la limite de {self.max_steps} étapes',
                    'plan': plan
                }

            # Phase 3: Afficher le plan et demander confirmation
            if callback:
                callback("plan_ready", plan)

            # À ce stade, l'interface doit demander confirmation
            # L'exécution se fera via execute_plan()

            return {
                'success': True,
                'plan': plan,
                'analysis': analysis,
                'ready_to_execute': True
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur tâche autonome: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            self.is_running = False

    def execute_plan(self, plan: Optional[Dict] = None) -> Dict:
        """
        Exécute un plan étape par étape

        Args:
            plan: Plan à exécuter (ou utilise current_plan)

        Returns:
            Dict avec résultat
        """
        plan = plan or self.current_plan

        if not plan:
            return {
                'success': False,
                'error': 'Aucun plan à exécuter'
            }

        # Initialiser results dès le début pour éviter les race conditions
        results = []
        project_path = None

        try:
            self.is_running = True
            self.is_paused = False
            self.current_step = 0

            # Déterminer le chemin du projet
            project_name = plan.get('project_name', 'mon_projet')
            base_path = self.executor.get_current_directory()
            project_path = os.path.join(base_path, project_name)

            # Contexte pour le code editor
            context = {
                'project_name': project_name,
                'dependencies': plan.get('dependencies', []),
                'project_type': plan.get('project_type', '')
            }

            if self.logger:
                self.logger.info(f"Démarrage exécution plan: {len(plan['steps'])} étapes")

            # Phase 2: Créer un snapshot avant l'exécution
            if os.path.exists(project_path):
                if self.logger:
                    self.logger.info(f"Création snapshot de sécurité pour: {project_path}")
                snapshot_result = self.rollback_manager.create_snapshot(
                    project_path,
                    f"Avant exécution: {plan.get('project_name', 'projet')}"
                )
                if snapshot_result['success']:
                    if self.logger:
                        self.logger.info(f"Snapshot créé: {snapshot_result['snapshot_id']}")
                else:
                    if self.logger:
                        self.logger.warning(f"Impossible de créer snapshot: {snapshot_result.get('error')}")

            # Analyser la parallélisation possible (Phase 1: Performance)
            parallel_groups = self.parallel_executor.can_parallelize(plan['steps'])
            parallel_stats = self.parallel_executor.get_parallelization_stats(plan['steps'])

            if self.logger:
                self.logger.info(f"Parallélisation: {parallel_stats['steps_parallelizable']} étapes sur {parallel_stats['total_steps']}")
                self.logger.info(f"Gain estimé: {parallel_stats['estimated_time_saving_percent']}%")

            # Exécuter par groupes parallélisables
            step_index = 0
            for group_idx, group_indices in enumerate(parallel_groups):
                # Vérifier timeout
                if self._check_timeout():
                    return {
                        'success': False,
                        'error': 'Timeout: durée maximale dépassée',
                        'results': results
                    }

                # Vérifier pause
                while self.is_paused:
                    time.sleep(0.5)
                    if self.on_pause:
                        self.on_pause()

                if not self.is_running:
                    return {
                        'success': False,
                        'stopped': True,
                        'message': 'Exécution arrêtée par l\'utilisateur',
                        'results': results
                    }

                # Récupérer les étapes de ce groupe
                group_steps = [plan['steps'][i] for i in group_indices]

                if len(group_steps) == 1:
                    # Une seule étape, exécution normale
                    step = group_steps[0]
                    i = group_indices[0] + 1
                    self.current_step = i

                    if self.on_step_start:
                        self.on_step_start(i, step)

                    step_result = self._execute_step(step, project_path, context)

                    results.append({
                        'step': i,
                        'action': step.get('action'),
                        'result': step_result
                    })

                    if self.on_step_complete:
                        self.on_step_complete(i, step, step_result)

                    if not step_result.get('success') and not step_result.get('can_continue'):
                        if self.on_error:
                            self.on_error(i, step, step_result)
                        return {
                            'success': False,
                            'error': f'Erreur à l\'étape {i}',
                            'step_error': step_result,
                            'results': results
                        }

                else:
                    # Plusieurs étapes, exécution parallèle!
                    if self.logger:
                        self.logger.info(f"⚡ Exécution parallèle de {len(group_steps)} étapes...")

                    # Notifier début pour toutes les étapes du groupe
                    for idx in group_indices:
                        i = idx + 1
                        if self.on_step_start:
                            self.on_step_start(i, plan['steps'][idx])

                    # Sérialiser les étapes pour les workers multiprocessing
                    serialized_steps = [
                        self._serialize_step_for_worker(step, project_path, context)
                        for step in group_steps
                    ]

                    # Exécuter en VRAI parallèle avec multiprocessing
                    # Utiliser le worker standalone qui est picklable
                    group_results = self.parallel_executor.execute_parallel(
                        serialized_steps,
                        parallel_workers.execute_step_worker
                    )

                    # Traiter les résultats
                    for idx, result in zip(group_indices, group_results):
                        i = idx + 1
                        step = plan['steps'][idx]

                        results.append({
                            'step': i,
                            'action': step.get('action'),
                            'result': result
                        })

                        if self.on_step_complete:
                            self.on_step_complete(i, step, result)

                        if not result.get('success') and not result.get('can_continue'):
                            if self.on_error:
                                self.on_error(i, step, result)
                            return {
                                'success': False,
                                'error': f'Erreur à l\'étape {i}',
                                'step_error': result,
                                'results': results
                            }

                # Petite pause entre les groupes
                time.sleep(0.5)

            # Succès!
            if self.logger:
                self.logger.info(f"Plan exécuté avec succès: {len(results)} étapes")

            return {
                'success': True,
                'message': 'Plan exécuté avec succès',
                'results': results,
                'project_path': project_path
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur exécution plan: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'results': results
            }
        finally:
            self.is_running = False
            self.is_paused = False

    def _serialize_step_for_worker(self, step: Dict, project_path: str, context: Dict) -> Dict:
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

    def _execute_step(self, step: Dict, project_path: str, context: Dict) -> Dict:
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
                return self._create_structure(step, project_path)

            elif action == 'create_file':
                return self._create_file(step, project_path, context)

            elif action == 'run_command':
                return self._run_command(step, project_path)

            elif action == 'git_commit':
                return self._git_commit(step, project_path)

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

    def _create_structure(self, step: Dict, project_path: str) -> Dict:
        """Crée la structure de dossiers"""
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

    def _create_file(self, step: Dict, project_path: str, context: Dict) -> Dict:
        """Crée un fichier avec du code généré"""
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

    def _run_command(self, step: Dict, project_path: str) -> Dict:
        """Exécute une commande avec retry automatique (Phase 3)"""
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

    def _git_commit(self, step: Dict, project_path: str) -> Dict:
        """Crée un commit Git"""
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

    def _check_timeout(self) -> bool:
        """Vérifie si le timeout est dépassé"""
        if not self.start_time:
            return False

        elapsed = datetime.now() - self.start_time
        return elapsed > self.max_duration

    def pause(self):
        """Met en pause l'exécution"""
        self.is_paused = True
        if self.logger:
            self.logger.info("Agent mis en pause")

    def resume(self):
        """Reprend l'exécution"""
        self.is_paused = False
        if self.logger:
            self.logger.info("Agent repris")

    def stop(self):
        """Arrête l'exécution"""
        self.is_running = False
        self.is_paused = False
        if self.logger:
            self.logger.info("Agent arrêté")

    def get_progress(self) -> Dict:
        """
        Retourne la progression actuelle

        Returns:
            Dict avec infos de progression
        """
        if not self.current_plan:
            return {
                'running': False
            }

        total_steps = len(self.current_plan.get('steps', []))
        progress_percent = (self.current_step / total_steps * 100) if total_steps > 0 else 0

        return {
            'running': self.is_running,
            'paused': self.is_paused,
            'current_step': self.current_step,
            'total_steps': total_steps,
            'progress_percent': progress_percent,
            'elapsed_time': (datetime.now() - self.start_time).seconds if self.start_time else 0
        }

    def rollback_last_execution(self, snapshot_id: Optional[str] = None) -> Dict:
        """
        Restaure un snapshot précédent (Phase 2: Rollback)

        Args:
            snapshot_id: ID du snapshot à restaurer (None = dernier)

        Returns:
            Dict avec résultat du rollback
        """
        if self.logger:
            self.logger.info(f"Tentative de rollback: {snapshot_id or 'dernier snapshot'}")

        result = self.rollback_manager.rollback(snapshot_id)

        if result['success']:
            if self.logger:
                self.logger.info(f"Rollback réussi: {result['project_path']}")
        else:
            if self.logger:
                self.logger.error(f"Rollback échoué: {result.get('error')}")

        return result

    def list_snapshots(self) -> list:
        """
        Liste tous les snapshots disponibles

        Returns:
            Liste des snapshots
        """
        return self.rollback_manager.list_snapshots()

    def get_rollback_stats(self) -> Dict:
        """
        Retourne les statistiques de rollback

        Returns:
            Dict avec les stats
        """
        return self.rollback_manager.get_total_snapshots_size()

    def get_correction_stats(self) -> Dict:
        """
        Retourne les statistiques d'auto-correction (Phase 3)

        Returns:
            Dict avec les stats
        """
        return self.auto_corrector.get_correction_stats()

    def get_last_error_analysis(self) -> Optional[Dict]:
        """
        Retourne l'analyse de la dernière erreur

        Returns:
            Dict avec l'analyse ou None
        """
        return self.auto_corrector.get_last_error_analysis()

    def analyze_error_with_ai(self, command: str, error: str) -> Dict:
        """
        Analyse une erreur avec l'IA pour obtenir des suggestions détaillées

        Args:
            command: Commande qui a échoué
            error: Message d'erreur

        Returns:
            Dict avec l'analyse IA
        """
        return self.auto_corrector.analyze_with_ai(command, error)
