"""Gestionnaire de rollback pour annuler les modifications de l'agent autonome"""

import os
import shutil
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import tempfile

class RollbackManager:
    """Gère les snapshots et le rollback des modifications"""

    def __init__(self, logger=None):
        """
        Initialise le gestionnaire de rollback

        Args:
            logger: Logger pour les messages
        """
        self.logger = logger

        # Répertoire pour les snapshots
        home_dir = Path.home()
        self.snapshots_dir = home_dir / ".terminal-ia" / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        # Snapshot actuel
        self.current_snapshot = None
        self.snapshot_metadata = {}

        # Limite de snapshots conservés
        self.max_snapshots = 10

        if self.logger:
            self.logger.info(f"RollbackManager initialisé: {self.snapshots_dir}")

    def create_snapshot(self, project_path: str, description: str = "") -> Dict[str, Any]:
        """
        Crée un snapshot d'un projet avant modification

        Args:
            project_path: Chemin du projet à sauvegarder
            description: Description du snapshot

        Returns:
            Dict avec les infos du snapshot
        """
        if not os.path.exists(project_path):
            return {
                'success': False,
                'error': f'Le chemin {project_path} n\'existe pas'
            }

        try:
            # Générer un ID unique pour le snapshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = os.path.basename(project_path)
            snapshot_id = f"{project_name}_{timestamp}"

            snapshot_path = self.snapshots_dir / snapshot_id
            snapshot_path.mkdir(parents=True, exist_ok=True)

            # Copier le projet
            if self.logger:
                self.logger.info(f"Création snapshot: {snapshot_id}")

            # Utiliser shutil.copytree pour copier récursivement
            backup_path = snapshot_path / "backup"
            shutil.copytree(project_path, backup_path, dirs_exist_ok=True)

            # Créer les métadonnées
            metadata = {
                'snapshot_id': snapshot_id,
                'project_path': project_path,
                'project_name': project_name,
                'description': description,
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'backup_path': str(backup_path)
            }

            # Sauvegarder les métadonnées
            metadata_file = snapshot_path / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            # Mettre à jour le snapshot actuel
            self.current_snapshot = snapshot_id
            self.snapshot_metadata = metadata

            # Nettoyer les anciens snapshots
            self._cleanup_old_snapshots()

            if self.logger:
                self.logger.info(f"Snapshot créé: {snapshot_id}")

            return {
                'success': True,
                'snapshot_id': snapshot_id,
                'metadata': metadata
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur création snapshot: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def rollback(self, snapshot_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Restaure un snapshot

        Args:
            snapshot_id: ID du snapshot à restaurer (None = dernier snapshot)

        Returns:
            Dict avec le résultat
        """
        # Utiliser le dernier snapshot si non spécifié
        if snapshot_id is None:
            snapshot_id = self.current_snapshot

        if not snapshot_id:
            return {
                'success': False,
                'error': 'Aucun snapshot disponible'
            }

        snapshot_path = self.snapshots_dir / snapshot_id
        metadata_file = snapshot_path / "metadata.json"

        if not metadata_file.exists():
            return {
                'success': False,
                'error': f'Snapshot {snapshot_id} introuvable'
            }

        try:
            # Charger les métadonnées
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            project_path = metadata['project_path']
            backup_path = metadata['backup_path']

            if self.logger:
                self.logger.info(f"Rollback vers snapshot: {snapshot_id}")

            # Supprimer le projet actuel
            if os.path.exists(project_path):
                shutil.rmtree(project_path)

            # Restaurer depuis le backup
            shutil.copytree(backup_path, project_path, dirs_exist_ok=True)

            if self.logger:
                self.logger.info(f"Rollback effectué: {project_path}")

            return {
                'success': True,
                'snapshot_id': snapshot_id,
                'project_path': project_path,
                'metadata': metadata
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur rollback: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        Liste tous les snapshots disponibles

        Returns:
            Liste des snapshots avec métadonnées
        """
        snapshots = []

        try:
            for snapshot_dir in sorted(self.snapshots_dir.iterdir(), reverse=True):
                if not snapshot_dir.is_dir():
                    continue

                metadata_file = snapshot_dir / "metadata.json"
                if not metadata_file.exists():
                    continue

                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    snapshots.append(metadata)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Erreur lecture metadata {snapshot_dir}: {e}")

            return snapshots

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur listage snapshots: {e}")
            return []

    def delete_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Supprime un snapshot

        Args:
            snapshot_id: ID du snapshot à supprimer

        Returns:
            Dict avec le résultat
        """
        snapshot_path = self.snapshots_dir / snapshot_id

        if not snapshot_path.exists():
            return {
                'success': False,
                'error': f'Snapshot {snapshot_id} introuvable'
            }

        try:
            shutil.rmtree(snapshot_path)

            if self.logger:
                self.logger.info(f"Snapshot supprimé: {snapshot_id}")

            # Si c'était le snapshot actuel, le réinitialiser
            if self.current_snapshot == snapshot_id:
                self.current_snapshot = None
                self.snapshot_metadata = {}

            return {
                'success': True,
                'snapshot_id': snapshot_id
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur suppression snapshot: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _cleanup_old_snapshots(self):
        """Nettoie les anciens snapshots si limite dépassée"""
        try:
            snapshots = self.list_snapshots()

            if len(snapshots) > self.max_snapshots:
                # Trier par date (plus ancien en premier)
                snapshots.sort(key=lambda x: x['timestamp'])

                # Supprimer les plus anciens
                to_delete = len(snapshots) - self.max_snapshots
                for i in range(to_delete):
                    snapshot_id = snapshots[i]['snapshot_id']
                    self.delete_snapshot(snapshot_id)

                if self.logger:
                    self.logger.info(f"Nettoyage: {to_delete} anciens snapshots supprimés")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Erreur nettoyage snapshots: {e}")

    def get_snapshot_size(self, snapshot_id: str) -> int:
        """
        Calcule la taille d'un snapshot en bytes

        Args:
            snapshot_id: ID du snapshot

        Returns:
            Taille en bytes
        """
        snapshot_path = self.snapshots_dir / snapshot_id

        if not snapshot_path.exists():
            return 0

        total_size = 0
        for dirpath, dirnames, filenames in os.walk(snapshot_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)

        return total_size

    def get_total_snapshots_size(self) -> Dict[str, Any]:
        """
        Calcule la taille totale de tous les snapshots

        Returns:
            Dict avec les statistiques
        """
        snapshots = self.list_snapshots()
        total_size = 0

        for snapshot in snapshots:
            snapshot_id = snapshot['snapshot_id']
            size = self.get_snapshot_size(snapshot_id)
            total_size += size

        return {
            'count': len(snapshots),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'snapshots_dir': str(self.snapshots_dir)
        }

    def clear_all_snapshots(self) -> Dict[str, Any]:
        """
        Supprime tous les snapshots

        Returns:
            Dict avec le résultat
        """
        try:
            snapshots = self.list_snapshots()
            count = len(snapshots)

            for snapshot in snapshots:
                snapshot_id = snapshot['snapshot_id']
                self.delete_snapshot(snapshot_id)

            self.current_snapshot = None
            self.snapshot_metadata = {}

            if self.logger:
                self.logger.info(f"Tous les snapshots supprimés: {count}")

            return {
                'success': True,
                'count': count
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur suppression snapshots: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def has_current_snapshot(self) -> bool:
        """
        Vérifie si un snapshot actuel existe

        Returns:
            True si un snapshot actuel existe
        """
        return self.current_snapshot is not None

    def get_current_snapshot_info(self) -> Optional[Dict[str, Any]]:
        """
        Retourne les infos du snapshot actuel

        Returns:
            Dict avec les métadonnées ou None
        """
        if not self.current_snapshot:
            return None

        return self.snapshot_metadata
