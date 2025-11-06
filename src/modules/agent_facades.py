"""
Agent Facades - Interfaces vers les services de rollback et auto-correction

Ce module fournit des interfaces propres vers:
- RollbackManager: Snapshots et restauration
- AutoCorrector: Analyse d'erreurs et corrections
"""

from typing import Dict, Optional, List
from ..utils.rollback_manager import RollbackManager
from ..utils.auto_corrector import AutoCorrector


class RollbackFacade:
    """Interface vers le gestionnaire de rollback"""

    def __init__(self, rollback_manager: RollbackManager, logger=None):
        """
        Initialise la facade de rollback

        Args:
            rollback_manager: Gestionnaire de rollback
            logger: Logger optionnel
        """
        self.rollback_manager = rollback_manager
        self.logger = logger

    def create_snapshot(self, project_path: str, plan: Dict) -> Dict:
        """
        Crée un snapshot avant l'exécution d'un plan

        Args:
            project_path: Chemin du projet
            plan: Plan à exécuter

        Returns:
            Résultat de la création du snapshot
        """
        if self.logger:
            self.logger.info(f"Création snapshot pour: {project_path}")

        result = self.rollback_manager.create_snapshot(
            project_path=project_path,
            plan=plan
        )

        if result['success']:
            if self.logger:
                self.logger.info(f"Snapshot créé: {result['snapshot_id']}")
        else:
            if self.logger:
                self.logger.warning(f"Impossible de créer snapshot: {result.get('error')}")

        return result

    def rollback(self, snapshot_id: Optional[str] = None) -> Dict:
        """
        Restaure un snapshot précédent

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

    def list_snapshots(self) -> List[Dict]:
        """
        Liste tous les snapshots disponibles

        Returns:
            Liste des snapshots
        """
        return self.rollback_manager.list_snapshots()

    def get_stats(self) -> Dict:
        """
        Retourne les statistiques de rollback

        Returns:
            Dict avec les stats
        """
        return self.rollback_manager.get_total_snapshots_size()


class CorrectionFacade:
    """Interface vers l'auto-correcteur"""

    def __init__(self, auto_corrector: AutoCorrector, logger=None):
        """
        Initialise la facade de correction

        Args:
            auto_corrector: Auto-correcteur
            logger: Logger optionnel
        """
        self.auto_corrector = auto_corrector
        self.logger = logger

    def analyze_error(self, command: str, error: str, exit_code: int = 1) -> Dict:
        """
        Analyse une erreur de commande

        Args:
            command: Commande qui a échoué
            error: Message d'erreur
            exit_code: Code de sortie

        Returns:
            Dict avec l'analyse
        """
        if self.logger:
            self.logger.debug(f"Analyse d'erreur pour: {command}")

        return self.auto_corrector.analyze_error(command, error, exit_code)

    def analyze_with_ai(self, command: str, error: str) -> Dict:
        """
        Analyse une erreur avec l'IA pour obtenir des suggestions détaillées

        Args:
            command: Commande qui a échoué
            error: Message d'erreur

        Returns:
            Dict avec l'analyse IA
        """
        if self.logger:
            self.logger.info(f"Analyse IA pour: {command}")

        return self.auto_corrector.analyze_with_ai(command, error)

    def get_stats(self) -> Dict:
        """
        Retourne les statistiques d'auto-correction

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
