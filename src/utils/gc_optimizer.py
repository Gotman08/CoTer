"""Optimiseur de Garbage Collection proactif (CSAPP Ch.9)

Ce module surveille la mémoire et déclenche le GC de manière proactive
pour éviter les pics de consommation mémoire sur systèmes à RAM limitée (Raspberry Pi).
"""

import gc
import psutil
import time
import threading
from typing import Dict, Any, Optional, Callable


class GCOptimizer:
    """Optimiseur de Garbage Collection pour systèmes à RAM limitée"""

    # Seuils de mémoire pour déclenchement GC proactif
    MEMORY_HIGH_THRESHOLD = 80    # 80% RAM utilisée = GC agressif
    MEMORY_WARNING_THRESHOLD = 70  # 70% RAM utilisée = GC normal
    MEMORY_LOW_THRESHOLD = 60     # <60% RAM = pas de GC proactif

    # Intervalles de monitoring
    MONITOR_INTERVAL_SECONDS = 5    # Vérifier toutes les 5 secondes
    GC_COOLDOWN_SECONDS = 10        # Attendre 10s entre deux GC

    def __init__(self, logger=None, auto_tune: bool = True,
                 thresholds: Optional[tuple[int, int, int]] = None):
        """
        Initialise l'optimiseur GC

        Args:
            logger: Logger optionnel
            auto_tune: Si True, ajuste automatiquement les seuils GC selon RAM
            thresholds: Seuils GC personnalisés (gen0, gen1, gen2)
        """
        self.logger = logger
        self.auto_tune = auto_tune

        # État du moniteur
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._last_gc_time = 0
        self._gc_count = 0
        self._forced_gc_count = 0

        # Stats
        self._stats = {
            'total_collections': 0,
            'forced_collections': 0,
            'memory_freed_mb': 0.0,
            'average_duration_ms': 0.0,
            'last_gc_duration_ms': 0.0
        }

        # Callbacks
        self.on_gc_trigger: Optional[Callable[[Dict], None]] = None

        # Configurer GC
        if thresholds:
            gc.set_threshold(*thresholds)
            if self.logger:
                self.logger.info(f"GC thresholds configurés: {thresholds}")
        elif auto_tune:
            self._auto_tune_gc()

        if self.logger:
            self.logger.info("GCOptimizer initialisé")

    def _auto_tune_gc(self):
        """Configure automatiquement les seuils GC selon la RAM disponible (CSAPP Ch.9)"""
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)

        if ram_gb < 2:
            # Très peu de RAM: GC très agressif
            thresholds = (400, 5, 5)
        elif ram_gb < 4:
            # Peu de RAM: GC agressif
            thresholds = (500, 8, 8)
        elif ram_gb < 8:
            # RAM moyenne: GC normal
            thresholds = (600, 10, 10)
        else:
            # Beaucoup de RAM: GC relaxé
            thresholds = (700, 10, 10)

        gc.set_threshold(*thresholds)

        if self.logger:
            self.logger.info(f"GC auto-tuné pour {ram_gb:.1f}GB RAM: {thresholds}")

    def get_memory_pressure(self) -> Dict[str, Any]:
        """
        Évalue la pression mémoire actuelle

        Returns:
            Dict avec infos de pression mémoire
        """
        memory = psutil.virtual_memory()
        percent = memory.percent

        if percent >= self.MEMORY_HIGH_THRESHOLD:
            level = 'high'
            should_gc = True
            aggressive = True
        elif percent >= self.MEMORY_WARNING_THRESHOLD:
            level = 'warning'
            should_gc = True
            aggressive = False
        elif percent >= self.MEMORY_LOW_THRESHOLD:
            level = 'normal'
            should_gc = False
            aggressive = False
        else:
            level = 'low'
            should_gc = False
            aggressive = False

        return {
            'level': level,
            'percent': percent,
            'available_mb': memory.available / (1024 * 1024),
            'used_mb': memory.used / (1024 * 1024),
            'total_mb': memory.total / (1024 * 1024),
            'should_gc': should_gc,
            'aggressive': aggressive
        }

    def force_gc(self, aggressive: bool = False) -> Dict[str, Any]:
        """
        Force un garbage collection

        Args:
            aggressive: Si True, collecte toutes les générations

        Returns:
            Dict avec résultats du GC
        """
        # Cooldown pour éviter GC trop fréquents
        now = time.time()
        if now - self._last_gc_time < self.GC_COOLDOWN_SECONDS:
            if self.logger:
                self.logger.debug("GC ignoré (cooldown actif)")
            return {'skipped': True, 'reason': 'cooldown'}

        # Mesurer mémoire avant
        mem_before = psutil.virtual_memory().used

        # Lancer GC
        start_time = time.time()

        if aggressive:
            # Collecter toutes les générations
            gc.collect(2)  # Generation 2 (collecte tout)
        else:
            # Collecter génération 0 seulement
            gc.collect(0)

        duration = (time.time() - start_time) * 1000  # ms

        # Mesurer mémoire après
        mem_after = psutil.virtual_memory().used
        freed_mb = (mem_before - mem_after) / (1024 * 1024)

        # Mettre à jour stats
        self._last_gc_time = now
        self._gc_count += 1
        self._forced_gc_count += 1

        self._stats['total_collections'] = self._gc_count
        self._stats['forced_collections'] = self._forced_gc_count
        self._stats['memory_freed_mb'] += freed_mb
        self._stats['last_gc_duration_ms'] = duration

        # Moyenne mobile
        if self._gc_count > 0:
            old_avg = self._stats['average_duration_ms']
            self._stats['average_duration_ms'] = (old_avg * (self._gc_count - 1) + duration) / self._gc_count

        result = {
            'skipped': False,
            'aggressive': aggressive,
            'duration_ms': round(duration, 2),
            'freed_mb': round(freed_mb, 2),
            'generation': 2 if aggressive else 0
        }

        if self.logger:
            self.logger.debug(f"GC forcé: {freed_mb:.2f}MB libérés en {duration:.2f}ms")

        # Callback
        if self.on_gc_trigger:
            self.on_gc_trigger(result)

        return result

    def _monitor_loop(self):
        """Boucle de monitoring de la mémoire"""
        if self.logger:
            self.logger.info("Monitoring GC démarré")

        while self._monitoring:
            try:
                # Évaluer pression mémoire
                pressure = self.get_memory_pressure()

                if pressure['should_gc']:
                    if self.logger:
                        self.logger.debug(f"Pression mémoire: {pressure['level']} ({pressure['percent']:.1f}%)")

                    # Déclencher GC si nécessaire
                    self.force_gc(aggressive=pressure['aggressive'])

                # Attendre avant prochaine vérification
                time.sleep(self.MONITOR_INTERVAL_SECONDS)

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Erreur monitoring GC: {e}", exc_info=True)
                time.sleep(self.MONITOR_INTERVAL_SECONDS)

        if self.logger:
            self.logger.info("Monitoring GC arrêté")

    def start_monitoring(self):
        """Démarre le monitoring automatique de la mémoire"""
        if self._monitoring:
            if self.logger:
                self.logger.warning("Monitoring GC déjà actif")
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        if self.logger:
            self.logger.info("Monitoring GC activé")

    def stop_monitoring(self):
        """Arrête le monitoring automatique"""
        if not self._monitoring:
            return

        self._monitoring = False

        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
            self._monitor_thread = None

        if self.logger:
            self.logger.info("Monitoring GC désactivé")

    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du GC

        Returns:
            Dict avec les stats
        """
        gc_stats = gc.get_stats()
        thresholds = gc.get_threshold()
        counts = gc.get_count()

        return {
            'enabled': gc.isenabled(),
            'monitoring': self._monitoring,
            'thresholds': thresholds,
            'counts': counts,
            'collections': self._stats['total_collections'],
            'forced_collections': self._stats['forced_collections'],
            'memory_freed_mb': round(self._stats['memory_freed_mb'], 2),
            'average_duration_ms': round(self._stats['average_duration_ms'], 2),
            'last_duration_ms': round(self._stats['last_gc_duration_ms'], 2),
            'gc_stats': gc_stats
        }

    def get_report(self) -> str:
        """
        Génère un rapport sur l'état du GC

        Returns:
            Rapport formaté
        """
        stats = self.get_stats()
        pressure = self.get_memory_pressure()

        lines = []
        lines.append("╔═══════════════════════════════════════════════════════╗")
        lines.append("║          GARBAGE COLLECTOR STATUS                    ║")
        lines.append("╠═══════════════════════════════════════════════════════╣")

        # État
        status = "✅ Activé" if stats['enabled'] else "❌ Désactivé"
        monitor_status = "✅ Actif" if stats['monitoring'] else "⚠️  Inactif"

        lines.append(f"║ GC: {status:<48} ║")
        lines.append(f"║ Monitoring: {monitor_status:<43} ║")

        # Seuils
        thresholds = stats['thresholds']
        lines.append(f"║ Thresholds: {thresholds}{' ' * (41 - len(str(thresholds)))}║")

        # Compteurs
        counts = stats['counts']
        lines.append(f"║ Counts: {counts}{' ' * (45 - len(str(counts)))}║")

        lines.append("╠═══════════════════════════════════════════════════════╣")

        # Stats collections
        lines.append(f"║ Collections totales: {stats['collections']:<31} ║")
        lines.append(f"║ Collections forcées: {stats['forced_collections']:<31} ║")
        lines.append(f"║ Mémoire libérée: {stats['memory_freed_mb']} MB{' ' * (30 - len(f'{stats['memory_freed_mb']} MB'))}║")
        lines.append(f"║ Durée moyenne: {stats['average_duration_ms']} ms{' ' * (33 - len(f'{stats['average_duration_ms']} ms'))}║")

        lines.append("╠═══════════════════════════════════════════════════════╣")

        # Pression mémoire
        pressure_icon = "🟢" if pressure['level'] == 'low' else "🟡" if pressure['level'] == 'normal' else "🟠" if pressure['level'] == 'warning' else "🔴"
        lines.append(f"║ Pression mémoire: {pressure_icon} {pressure['level'].upper()}{' ' * (32 - len(pressure['level']))}║")
        lines.append(f"║ RAM utilisée: {pressure['percent']:.1f}%{' ' * (38 - len(f'{pressure['percent']:.1f}%'))}║")
        lines.append(f"║ Disponible: {pressure['available_mb']:.0f} MB{' ' * (35 - len(f'{pressure['available_mb']:.0f} MB'))}║")

        lines.append("╚═══════════════════════════════════════════════════════╝")

        return '\n'.join(lines)

    def __enter__(self):
        """Support du context manager"""
        self.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Nettoyage automatique"""
        self.stop_monitoring()
        return False

    def __del__(self):
        """Nettoyage lors de la destruction"""
        self.stop_monitoring()
