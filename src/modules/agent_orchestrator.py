"""
Agent Orchestrator - Orchestration du workflow d'exécution

Ce module gère:
- L'exécution des plans (séquentielle et parallèle)
- Le workflow et l'état
- La coordination des étapes
- Le timeout et les pauses
"""

import time
from typing import Dict, Optional, Callable, List
from datetime import datetime, timedelta

from .step_executor import StepExecutor
from .agent_facades import RollbackFacade
from ..utils.parallel_executor import ParallelExecutor
from ..utils import parallel_workers
from config import constants


class AgentOrchestrator:
    """Orchestre l'exécution des plans de projet"""

    def __init__(self, step_executor: StepExecutor, rollback_facade: RollbackFacade,
                 parallel_executor: ParallelExecutor, logger=None):
        """
        Initialise l'orchestrateur

        Args:
            step_executor: Exécuteur d'étapes
            rollback_facade: Facade vers le rollback
            parallel_executor: Exécuteur parallèle
            logger: Logger optionnel
        """
        self.step_executor = step_executor
        self.rollback_facade = rollback_facade
        self.parallel_executor = parallel_executor
        self.logger = logger

        # État de l'orchestrateur
        self.is_running = False
        self.is_paused = False
        self.current_plan = None
        self.current_step = 0
        self.start_time = None
        self.max_steps = constants.MAX_AGENT_STEPS
        self.max_duration = timedelta(minutes=constants.MAX_AGENT_DURATION_MINUTES)

        # Callbacks pour l'interface
        self.on_step_start: Optional[Callable] = None
        self.on_step_complete: Optional[Callable] = None
        self.on_pause: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

    def execute_plan(self, plan: Dict, project_path: str, context: Dict) -> Dict:
        """
        Exécute un plan de projet

        Args:
            plan: Plan généré par le ProjectPlanner
            project_path: Chemin où créer le projet
            context: Contexte du projet

        Returns:
            Dict avec résultat de l'exécution
        """
        self.current_plan = plan
        self.is_running = True
        self.is_paused = False
        self.current_step = 0
        results = []

        try:
            if self.logger:
                self.logger.info(f"Démarrage exécution plan: {len(plan.get('steps', []))} étapes")

            # Créer snapshot avant l'exécution (Phase 2: Sécurité)
            if self.rollback_facade:
                snapshot_result = self.rollback_facade.create_snapshot(project_path, plan)

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

                    step_result = self.step_executor.execute_step(step, project_path, context)

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
                        self.step_executor.serialize_step_for_worker(step, project_path, context)
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

    def _check_timeout(self) -> bool:
        """
        Vérifie si le timeout est dépassé

        Returns:
            True si timeout dépassé
        """
        if not self.start_time:
            return False

        elapsed = datetime.now() - self.start_time
        return elapsed > self.max_duration

    def pause(self):
        """Met en pause l'exécution"""
        self.is_paused = True
        if self.logger:
            self.logger.info("Orchestrateur mis en pause")

    def resume(self):
        """Reprend l'exécution"""
        self.is_paused = False
        if self.logger:
            self.logger.info("Orchestrateur repris")

    def stop(self):
        """Arrête l'exécution"""
        self.is_running = False
        self.is_paused = False
        if self.logger:
            self.logger.info("Orchestrateur arrêté")

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
