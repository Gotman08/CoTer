"""Gestionnaire de cache pour les réponses Ollama"""

import hashlib
import json
import time
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class CacheManager:
    """Gère le cache des réponses Ollama pour améliorer les performances"""

    def __init__(self, cache_config, logger=None):
        """
        Initialise le gestionnaire de cache

        Args:
            cache_config: Configuration du cache
            logger: Logger pour les messages
        """
        self.config = cache_config
        self.logger = logger
        self.enabled = cache_config.cache_enabled

        if self.enabled:
            self._init_database()
            if self.logger:
                self.logger.info(f"Cache activé: {self.config.cache_dir}")

    def _init_database(self):
        """Initialise la base de données SQLite pour le cache"""
        db_path = self.config.ollama_cache_file

        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.cursor = self.conn.cursor()

        # Créer la table si elle n'existe pas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                prompt_hash TEXT NOT NULL,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                model TEXT NOT NULL,
                timestamp REAL NOT NULL,
                access_count INTEGER DEFAULT 0,
                last_accessed REAL NOT NULL,
                size_bytes INTEGER NOT NULL
            )
        ''')

        # Index pour optimiser les recherches
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_model ON cache(model)
        ''')

        self.conn.commit()

        # Nettoyage initial
        self._cleanup_expired()

    def _generate_cache_key(self, prompt: str, model: str, system_prompt: Optional[str] = None) -> str:
        """
        Génère une clé de cache unique pour un prompt

        Args:
            prompt: Le prompt utilisateur
            model: Le modèle utilisé
            system_prompt: Prompt système optionnel

        Returns:
            Clé de cache (hash)
        """
        # Combiner tous les paramètres qui influencent la réponse
        cache_string = f"{model}|{prompt}"
        if system_prompt:
            cache_string += f"|{system_prompt}"

        # Générer un hash SHA256
        hash_obj = hashlib.sha256(cache_string.encode('utf-8'))
        return hash_obj.hexdigest()

    def get(self, prompt: str, model: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Récupère une réponse du cache

        Args:
            prompt: Le prompt utilisateur
            model: Le modèle utilisé
            system_prompt: Prompt système optionnel

        Returns:
            Réponse cachée ou None si pas trouvé
        """
        if not self.enabled:
            return None

        cache_key = self._generate_cache_key(prompt, model, system_prompt)

        try:
            self.cursor.execute('''
                SELECT response, timestamp FROM cache WHERE key = ?
            ''', (cache_key,))

            result = self.cursor.fetchone()

            if result:
                response, timestamp = result
                age_hours = (time.time() - timestamp) / 3600

                # Vérifier si le cache est encore valide
                if age_hours < self.config.cache_ttl_hours:
                    # Mettre à jour les statistiques d'accès
                    self._update_access_stats(cache_key)

                    if self.logger:
                        self.logger.debug(f"Cache HIT: {cache_key[:16]}... (age: {age_hours:.1f}h)")

                    return response
                else:
                    # Cache expiré, le supprimer
                    self._delete(cache_key)
                    if self.logger:
                        self.logger.debug(f"Cache EXPIRED: {cache_key[:16]}...")

            return None

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur lecture cache: {e}")
            return None

    def set(self, prompt: str, response: str, model: str, system_prompt: Optional[str] = None):
        """
        Stocke une réponse dans le cache

        Args:
            prompt: Le prompt utilisateur
            response: La réponse à cacher
            model: Le modèle utilisé
            system_prompt: Prompt système optionnel
        """
        if not self.enabled:
            return

        cache_key = self._generate_cache_key(prompt, model, system_prompt)
        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
        current_time = time.time()
        size_bytes = len(response.encode('utf-8'))

        try:
            # Vérifier la taille du cache et nettoyer si nécessaire
            self._check_cache_size()

            # Insérer ou remplacer
            self.cursor.execute('''
                INSERT OR REPLACE INTO cache
                (key, prompt_hash, prompt, response, model, timestamp, access_count, last_accessed, size_bytes)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
            ''', (cache_key, prompt_hash, prompt, response, model, current_time, current_time, size_bytes))

            self.conn.commit()

            if self.logger:
                self.logger.debug(f"Cache SET: {cache_key[:16]}... ({size_bytes} bytes)")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur écriture cache: {e}")

    def _update_access_stats(self, cache_key: str):
        """Met à jour les statistiques d'accès pour une entrée"""
        try:
            current_time = time.time()
            self.cursor.execute('''
                UPDATE cache
                SET access_count = access_count + 1, last_accessed = ?
                WHERE key = ?
            ''', (current_time, cache_key))
            self.conn.commit()
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Erreur mise à jour stats cache: {e}")

    def _delete(self, cache_key: str):
        """Supprime une entrée du cache"""
        try:
            self.cursor.execute('DELETE FROM cache WHERE key = ?', (cache_key,))
            self.conn.commit()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur suppression cache: {e}")

    def _cleanup_expired(self):
        """Nettoie les entrées expirées du cache"""
        try:
            cutoff_time = time.time() - (self.config.cache_ttl_hours * 3600)

            self.cursor.execute('DELETE FROM cache WHERE timestamp < ?', (cutoff_time,))
            deleted = self.cursor.rowcount
            self.conn.commit()

            if deleted > 0 and self.logger:
                self.logger.info(f"Nettoyage cache: {deleted} entrées expirées supprimées")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur nettoyage cache: {e}")

    def _check_cache_size(self):
        """Vérifie la taille du cache et nettoie si nécessaire"""
        try:
            # Calculer la taille totale
            self.cursor.execute('SELECT SUM(size_bytes) FROM cache')
            total_size = self.cursor.fetchone()[0] or 0
            total_size_mb = total_size / (1024 * 1024)

            # Si dépasse la limite, supprimer selon stratégie
            if total_size_mb > self.config.max_cache_size_mb:
                self._evict_entries()

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur vérification taille cache: {e}")

    def _evict_entries(self):
        """Supprime des entrées selon la stratégie d'éviction"""
        try:
            # Calculer combien supprimer (20% du cache)
            self.cursor.execute('SELECT COUNT(*) FROM cache')
            total_entries = self.cursor.fetchone()[0]
            entries_to_remove = max(1, int(total_entries * 0.2))

            if self.config.eviction_strategy == 'lru':
                # Least Recently Used
                self.cursor.execute('''
                    DELETE FROM cache WHERE key IN (
                        SELECT key FROM cache ORDER BY last_accessed ASC LIMIT ?
                    )
                ''', (entries_to_remove,))
            elif self.config.eviction_strategy == 'lfu':
                # Least Frequently Used
                self.cursor.execute('''
                    DELETE FROM cache WHERE key IN (
                        SELECT key FROM cache ORDER BY access_count ASC LIMIT ?
                    )
                ''', (entries_to_remove,))
            else:  # fifo
                # First In First Out
                self.cursor.execute('''
                    DELETE FROM cache WHERE key IN (
                        SELECT key FROM cache ORDER BY timestamp ASC LIMIT ?
                    )
                ''', (entries_to_remove,))

            deleted = self.cursor.rowcount
            self.conn.commit()

            if self.logger:
                self.logger.info(f"Éviction cache: {deleted} entrées supprimées ({self.config.eviction_strategy})")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur éviction cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache

        Returns:
            Dict avec les statistiques
        """
        if not self.enabled:
            return {'enabled': False}

        try:
            # Nombre total d'entrées
            self.cursor.execute('SELECT COUNT(*) FROM cache')
            total_entries = self.cursor.fetchone()[0]

            # Taille totale
            self.cursor.execute('SELECT SUM(size_bytes) FROM cache')
            total_size = self.cursor.fetchone()[0] or 0
            total_size_mb = total_size / (1024 * 1024)

            # Entrée la plus récente
            self.cursor.execute('SELECT MAX(timestamp) FROM cache')
            latest_timestamp = self.cursor.fetchone()[0]

            # Entrée la plus ancienne
            self.cursor.execute('SELECT MIN(timestamp) FROM cache')
            oldest_timestamp = self.cursor.fetchone()[0]

            # Total des accès
            self.cursor.execute('SELECT SUM(access_count) FROM cache')
            total_accesses = self.cursor.fetchone()[0] or 0

            # Hit rate (approximatif)
            hit_rate = (total_accesses / total_entries * 100) if total_entries > 0 else 0

            return {
                'enabled': True,
                'total_entries': total_entries,
                'total_size_mb': round(total_size_mb, 2),
                'max_size_mb': self.config.max_cache_size_mb,
                'usage_percent': round((total_size_mb / self.config.max_cache_size_mb) * 100, 1),
                'total_accesses': total_accesses,
                'hit_rate_approx': round(hit_rate, 1),
                'oldest_entry': datetime.fromtimestamp(oldest_timestamp).isoformat() if oldest_timestamp else None,
                'latest_entry': datetime.fromtimestamp(latest_timestamp).isoformat() if latest_timestamp else None,
                'ttl_hours': self.config.cache_ttl_hours,
                'eviction_strategy': self.config.eviction_strategy
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur stats cache: {e}")
            return {'enabled': True, 'error': str(e)}

    def clear(self):
        """Efface tout le cache"""
        try:
            self.cursor.execute('DELETE FROM cache')
            self.conn.commit()

            if self.logger:
                self.logger.info("Cache complètement effacé")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur effacement cache: {e}")

    def close(self):
        """Ferme la connexion à la base de données"""
        if hasattr(self, 'conn'):
            self.conn.close()
