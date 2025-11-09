"""Module de stockage persistant des plans générés en arrière-plan"""

import sqlite3
import json
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from pathlib import Path
from config.constants import APP_DIR


class PlanStorage:
    """
    Stockage SQLite pour les plans générés en arrière-plan.
    Permet de conserver l'historique des plans et de les consulter via /plan
    """

    def __init__(self, db_path: Optional[Path] = None, logger=None):
        """
        Initialise le stockage des plans

        Args:
            db_path: Chemin de la base SQLite (par défaut: ~/.terminal-ia/plans.db)
            logger: Logger optionnel
        """
        self.logger = logger

        # Chemin de la base de données
        if db_path is None:
            plans_dir = APP_DIR / "plans"
            plans_dir.mkdir(parents=True, exist_ok=True)
            db_path = plans_dir / "background_plans.db"

        self.db_path = Path(db_path)

        # Créer les tables si nécessaire
        self._initialize_database()

        if self.logger:
            self.logger.info(f"PlanStorage initialisé: {self.db_path}")

    def _initialize_database(self):
        """Crée les tables de la base de données"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Table des plans
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE,
                user_request TEXT NOT NULL,
                analysis JSON NOT NULL,
                plan JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed BOOLEAN DEFAULT 0,
                executed_at TIMESTAMP,
                execution_status TEXT,
                planning_time_seconds REAL
            )
        ''')

        # Index pour recherche rapide
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON plans(created_at DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_executed ON plans(executed)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_request_id ON plans(request_id)
        ''')

        conn.commit()
        conn.close()

    def save_plan(self, request_id: str, user_request: str, analysis: Dict, plan: Dict,
                  planning_time: Optional[float] = None) -> int:
        """
        Sauvegarde un plan généré

        Args:
            request_id: ID unique de la requête
            user_request: Requête utilisateur originale
            analysis: Résultat de l'analyse
            plan: Plan généré
            planning_time: Temps de génération en secondes

        Returns:
            ID du plan inséré
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO plans (request_id, user_request, analysis, plan, planning_time_seconds)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                request_id,
                user_request,
                json.dumps(analysis),
                json.dumps(plan),
                planning_time
            ))

            plan_id = cursor.lastrowid
            conn.commit()

            if self.logger:
                self.logger.debug(f"Plan sauvegardé: ID={plan_id}, request_id={request_id}")

            return plan_id

        except sqlite3.IntegrityError:
            # request_id déjà existe, mise à jour
            cursor.execute('''
                UPDATE plans
                SET user_request=?, analysis=?, plan=?, planning_time_seconds=?
                WHERE request_id=?
            ''', (
                user_request,
                json.dumps(analysis),
                json.dumps(plan),
                planning_time,
                request_id
            ))

            conn.commit()

            if self.logger:
                self.logger.debug(f"Plan mis à jour: request_id={request_id}")

            # Récupérer l'ID
            cursor.execute('SELECT id FROM plans WHERE request_id=?', (request_id,))
            plan_id = cursor.fetchone()[0]
            return plan_id

        finally:
            conn.close()

    def get_plan(self, plan_id: int) -> Optional[Dict]:
        """
        Récupère un plan par son ID

        Args:
            plan_id: ID du plan

        Returns:
            Dict avec les données du plan ou None
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM plans WHERE id=?', (plan_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_dict(row)
        return None

    def get_latest_plan(self, executed: Optional[bool] = None) -> Optional[Dict]:
        """
        Récupère le plan le plus récent

        Args:
            executed: Si spécifié, filtre par statut d'exécution

        Returns:
            Dict avec les données du plan ou None
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if executed is None:
            cursor.execute('SELECT * FROM plans ORDER BY created_at DESC LIMIT 1')
        else:
            cursor.execute(
                'SELECT * FROM plans WHERE executed=? ORDER BY created_at DESC LIMIT 1',
                (1 if executed else 0,)
            )

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_dict(row)
        return None

    def get_recent_plans(self, limit: int = 10, executed: Optional[bool] = None) -> List[Dict]:
        """
        Récupère les plans récents

        Args:
            limit: Nombre maximum de plans à récupérer
            executed: Si spécifié, filtre par statut d'exécution

        Returns:
            Liste de dicts avec les données des plans
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if executed is None:
            cursor.execute('SELECT * FROM plans ORDER BY created_at DESC LIMIT ?', (limit,))
        else:
            cursor.execute(
                'SELECT * FROM plans WHERE executed=? ORDER BY created_at DESC LIMIT ?',
                (1 if executed else 0, limit)
            )

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_dict(row) for row in rows]

    def mark_executed(self, plan_id: int, status: str = 'success') -> bool:
        """
        Marque un plan comme exécuté

        Args:
            plan_id: ID du plan
            status: Statut d'exécution ('success', 'failed', 'partial')

        Returns:
            True si mis à jour, False sinon
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE plans
            SET executed=1, executed_at=CURRENT_TIMESTAMP, execution_status=?
            WHERE id=?
        ''', (status, plan_id))

        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if self.logger and updated:
            self.logger.info(f"Plan {plan_id} marqué comme exécuté: {status}")

        return updated

    def cleanup_old_plans(self, days: int = 7) -> int:
        """
        Supprime les plans plus anciens que N jours

        Args:
            days: Nombre de jours à conserver

        Returns:
            Nombre de plans supprimés
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)

        cursor.execute(
            'DELETE FROM plans WHERE created_at < ?',
            (cutoff_date.isoformat(),)
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if self.logger and deleted > 0:
            self.logger.info(f"{deleted} plans supprimés (>{days} jours)")

        return deleted

    def get_stats(self) -> Dict:
        """
        Récupère les statistiques du stockage

        Returns:
            Dict avec les statistiques
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Total de plans
        cursor.execute('SELECT COUNT(*) FROM plans')
        total = cursor.fetchone()[0]

        # Plans exécutés
        cursor.execute('SELECT COUNT(*) FROM plans WHERE executed=1')
        executed = cursor.fetchone()[0]

        # Plans non exécutés
        cursor.execute('SELECT COUNT(*) FROM plans WHERE executed=0')
        pending = cursor.fetchone()[0]

        # Temps moyen de planification
        cursor.execute('SELECT AVG(planning_time_seconds) FROM plans WHERE planning_time_seconds IS NOT NULL')
        avg_time = cursor.fetchone()[0] or 0.0

        # Plan le plus ancien
        cursor.execute('SELECT MIN(created_at) FROM plans')
        oldest = cursor.fetchone()[0]

        conn.close()

        return {
            'total_plans': total,
            'executed': executed,
            'pending': pending,
            'avg_planning_time': round(avg_time, 2),
            'oldest_plan': oldest,
            'db_path': str(self.db_path)
        }

    def search_plans(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Recherche des plans par mots-clés dans la requête utilisateur

        Args:
            query: Requête de recherche
            limit: Nombre maximum de résultats

        Returns:
            Liste de plans correspondants
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM plans
            WHERE user_request LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (f'%{query}%', limit))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_dict(row) for row in rows]

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """
        Convertit une ligne SQLite en dictionnaire

        Args:
            row: Ligne SQLite

        Returns:
            Dict avec les données
        """
        return {
            'id': row['id'],
            'request_id': row['request_id'],
            'user_request': row['user_request'],
            'analysis': json.loads(row['analysis']),
            'plan': json.loads(row['plan']),
            'created_at': row['created_at'],
            'executed': bool(row['executed']),
            'executed_at': row['executed_at'],
            'execution_status': row['execution_status'],
            'planning_time': row['planning_time_seconds']
        }

    def clear_all(self):
        """Supprime TOUS les plans (attention !)"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute('DELETE FROM plans')
        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        if self.logger:
            self.logger.warning(f"TOUS les plans supprimés ({deleted} plans)")

        return deleted
