"""Configuration du système de cache pour Ollama"""

import os
from pathlib import Path

class CacheConfig:
    """Configuration du cache Ollama"""

    def __init__(self):
        # Chemins
        home_dir = Path.home()
        self.cache_dir = home_dir / ".terminal-ia" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Fichiers de cache
        self.ollama_cache_file = self.cache_dir / "ollama_responses.db"
        self.metadata_file = self.cache_dir / "cache_metadata.json"

        # Configuration du cache
        self.cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        self.cache_ttl_hours = int(os.getenv("CACHE_TTL_HOURS", "24"))  # 24h par défaut
        self.max_cache_size_mb = int(os.getenv("MAX_CACHE_SIZE_MB", "500"))  # 500 MB max
        self.cache_compression = os.getenv("CACHE_COMPRESSION", "true").lower() == "true"

        # Stratégie d'éviction
        self.eviction_strategy = os.getenv("CACHE_EVICTION", "lru")  # lru, lfu, fifo

        # Cache par type de requête
        self.cache_generate = True  # Cache pour génération de code
        self.cache_chat = True  # Cache pour conversations
        self.cache_analysis = True  # Cache pour analyse de demandes

        # Performance
        self.cache_async = False  # Écriture asynchrone (future feature)
        self.cache_preload = True  # Préchargement au démarrage

    def get_cache_path(self, cache_type: str = "default") -> Path:
        """
        Retourne le chemin du fichier de cache pour un type donné

        Args:
            cache_type: Type de cache (default, code, chat, etc.)

        Returns:
            Path du fichier de cache
        """
        cache_file = self.cache_dir / f"{cache_type}_cache.db"
        return cache_file

    def clear_cache(self):
        """Efface tous les fichiers de cache"""
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_stats(self) -> dict:
        """
        Retourne les statistiques du cache

        Returns:
            Dict avec les stats
        """
        import os

        total_size = 0
        file_count = 0

        if self.cache_dir.exists():
            for file in self.cache_dir.rglob("*"):
                if file.is_file():
                    total_size += file.stat().st_size
                    file_count += 1

        return {
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count,
            'cache_dir': str(self.cache_dir),
            'enabled': self.cache_enabled
        }
