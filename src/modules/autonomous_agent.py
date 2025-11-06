"""
Agent autonome pour exécuter des tâches complexes automatiquement

Cette version est une façade qui délègue vers des modules spécialisés:
- StepExecutor: Exécution des actions individuelles
- AgentOrchestrator: Orchestration du workflow
- AgentFacades: Interfaces vers rollback et corrections
"""

from typing import Dict, Optional, Callable

from .project_planner import ProjectPlanner
from .code_editor import CodeEditor
from .git_manager import GitManager
from .command_executor import CommandExecutor
from .step_executor import StepExecutor
from .agent_orchestrator import AgentOrchestrator
from .agent_facades import RollbackFacade, CorrectionFacade
from ..utils.parallel_executor import ParallelExecutor
from ..utils.rollback_manager import RollbackManager
from ..utils.auto_corrector import AutoCorrector


class AutonomousAgent:
    """Agent autonome qui planifie et exécute des tâches complexes"""

    def __init__(self, ollama_client, executor: CommandExecutor, settings, logger=None):
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

        # Initialiser les modules de base
        self.planner = ProjectPlanner(ollama_client, logger)
        code_editor = CodeEditor(ollama_client, logger)
        git_manager = GitManager(ollama_client, logger)

        # Initialiser les services (Phase 1-3)
        parallel_executor = ParallelExecutor(logger=logger)
        rollback_manager = RollbackManager(logger=logger)
        auto_corrector = AutoCorrector(ollama_client=ollama_client, logger=logger)

        if self.logger:
            self.logger.info(f"Exécution parallèle activée avec {parallel_executor.max_workers} workers")
            self.logger.info("Gestionnaire de rollback initialisé")
            self.logger.info("Auto-correcteur initialisé")

        # Créer les facades
        self.rollback_facade = RollbackFacade(rollback_manager, logger)
        self.correction_facade = CorrectionFacade(auto_corrector, logger)

        # Créer l'exécuteur d'étapes
        self.step_executor = StepExecutor(
            executor=executor,
            code_editor=code_editor,
            git_manager=git_manager,
            auto_corrector=auto_corrector,
            logger=logger
        )

        # Créer l'orchestrateur
        self.orchestrator = AgentOrchestrator(
            step_executor=self.step_executor,
            rollback_facade=self.rollback_facade,
            parallel_executor=parallel_executor,
            logger=logger
        )

    # ========== Propriétés déléguées ==========

    @property
    def is_running(self) -> bool:
        """Indique si l'agent est en cours d'exécution"""
        return self.orchestrator.is_running

    @is_running.setter
    def is_running(self, value: bool):
        """Définit l'état d'exécution"""
        self.orchestrator.is_running = value

    @property
    def is_paused(self) -> bool:
        """Indique si l'agent est en pause"""
        return self.orchestrator.is_paused

    @is_paused.setter
    def is_paused(self, value: bool):
        """Définit l'état de pause"""
        self.orchestrator.is_paused = value

    @property
    def current_plan(self) -> Optional[Dict]:
        """Retourne le plan en cours"""
        return self.orchestrator.current_plan

    @current_plan.setter
    def current_plan(self, value: Optional[Dict]):
        """Définit le plan en cours"""
        self.orchestrator.current_plan = value

    @property
    def current_step(self) -> int:
        """Retourne l'étape courante"""
        return self.orchestrator.current_step

    @property
    def start_time(self):
        """Retourne l'heure de démarrage"""
        return self.orchestrator.start_time

    # ========== Callbacks ==========

    @property
    def on_step_start(self) -> Optional[Callable]:
        """Callback appelé au début de chaque étape"""
        return self.orchestrator.on_step_start

    @on_step_start.setter
    def on_step_start(self, callback: Optional[Callable]):
        """Définit le callback de début d'étape"""
        self.orchestrator.on_step_start = callback

    @property
    def on_step_complete(self) -> Optional[Callable]:
        """Callback appelé à la fin de chaque étape"""
        return self.orchestrator.on_step_complete

    @on_step_complete.setter
    def on_step_complete(self, callback: Optional[Callable]):
        """Définit le callback de fin d'étape"""
        self.orchestrator.on_step_complete = callback

    @property
    def on_error(self) -> Optional[Callable]:
        """Callback appelé en cas d'erreur"""
        return self.orchestrator.on_error

    @on_error.setter
    def on_error(self, callback: Optional[Callable]):
        """Définit le callback d'erreur"""
        self.orchestrator.on_error = callback

    @property
    def on_pause(self) -> Optional[Callable]:
        """Callback appelé lors d'une pause"""
        return self.orchestrator.on_pause

    @on_pause.setter
    def on_pause(self, callback: Optional[Callable]):
        """Définit le callback de pause"""
        self.orchestrator.on_pause = callback

    # ========== Méthodes publiques ==========

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
            self.orchestrator.start_time = __import__('datetime').datetime.now()

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
                callback("planning", "Génération du plan d'action...")

            plan = self.planner.generate_plan(user_request, analysis)

            if not plan or not plan.get('steps'):
                return {
                    'success': False,
                    'message': 'Impossible de générer un plan',
                    'plan': None
                }

            return {
                'success': True,
                'plan': plan,
                'analysis': analysis
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur tâche autonome: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def execute_plan(self, plan: Dict) -> Dict:
        """
        Exécute un plan de projet (délégué à l'orchestrateur)

        Args:
            plan: Plan généré par le ProjectPlanner

        Returns:
            Dict avec résultat de l'exécution
        """
        project_path = plan.get('project_path', './generated_project')
        context = plan.get('context', {})

        return self.orchestrator.execute_plan(plan, project_path, context)

    def pause(self):
        """Met en pause l'exécution (délégué à l'orchestrateur)"""
        self.orchestrator.pause()

    def resume(self):
        """Reprend l'exécution (délégué à l'orchestrateur)"""
        self.orchestrator.resume()

    def stop(self):
        """Arrête l'exécution (délégué à l'orchestrateur)"""
        self.orchestrator.stop()

    def get_progress(self) -> Dict:
        """
        Retourne la progression actuelle (délégué à l'orchestrateur)

        Returns:
            Dict avec infos de progression
        """
        return self.orchestrator.get_progress()

    # ========== Méthodes de facade vers RollbackManager ==========

    def rollback_last_execution(self, snapshot_id: Optional[str] = None) -> Dict:
        """
        Restaure un snapshot précédent

        Args:
            snapshot_id: ID du snapshot à restaurer (None = dernier)

        Returns:
            Dict avec résultat du rollback
        """
        return self.rollback_facade.rollback(snapshot_id)

    def list_snapshots(self) -> list:
        """
        Liste tous les snapshots disponibles

        Returns:
            Liste des snapshots
        """
        return self.rollback_facade.list_snapshots()

    def get_rollback_stats(self) -> Dict:
        """
        Retourne les statistiques de rollback

        Returns:
            Dict avec les stats
        """
        return self.rollback_facade.get_stats()

    # ========== Méthodes de facade vers AutoCorrector ==========

    def get_correction_stats(self) -> Dict:
        """
        Retourne les statistiques d'auto-correction

        Returns:
            Dict avec les stats
        """
        return self.correction_facade.get_stats()

    def get_last_error_analysis(self) -> Optional[Dict]:
        """
        Retourne l'analyse de la dernière erreur

        Returns:
            Dict avec l'analyse ou None
        """
        return self.correction_facade.get_last_error_analysis()

    def analyze_error_with_ai(self, command: str, error: str) -> Dict:
        """
        Analyse une erreur avec l'IA pour obtenir des suggestions détaillées

        Args:
            command: Commande qui a échoué
            error: Message d'erreur

        Returns:
            Dict avec l'analyse IA
        """
        return self.correction_facade.analyze_with_ai(command, error)
