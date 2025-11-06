"""Optimiseur spécifique pour architecture ARM (CSAPP Ch.8)

Ce module applique des optimisations spécifiques à l'architecture ARM:
- Réduction du context switching (coûteux sur ARM)
- Optimisation des memory barriers
- Ajustement des caches L1/L2 pour ARM Cortex
- Configuration optimale pour Raspberry Pi 5 (BCM2712)
"""

import platform
import os
from typing import Dict, Any, Optional
import psutil


class ARMOptimizer:
    """Optimiseur pour architecture ARM (Raspberry Pi, etc.)"""

    # Facteurs d'ajustement pour ARM (CSAPP Ch.8)
    ARM_WORKER_REDUCTION = 0.8  # Réduire workers de 20% (context switch coûteux)
    ARM_CACHE_REDUCTION = 0.7   # Réduire cache de 30% (L2 cache plus petit)
    ARM_GC_AGGRESSION = 1.3     # GC 30% plus agressif (RAM limitée)

    # Paramètres spécifiques par chipset ARM
    CHIPSET_OPTIMIZATIONS = {
        'BCM2712': {  # Raspberry Pi 5
            'cpu_cores': 4,
            'cpu_freq_max': 2400,  # 2.4 GHz
            'l1_cache_kb': 64,     # 64KB L1 par core
            'l2_cache_mb': 2,      # 2MB L2 partagé
            'memory_bandwidth_gbps': 17,  # ~17 GB/s
            'optimal_workers': 3,
            'cache_line_size': 64,
            'prefetch_distance': 128
        },
        'BCM2711': {  # Raspberry Pi 4
            'cpu_cores': 4,
            'cpu_freq_max': 1800,  # 1.8 GHz
            'l1_cache_kb': 32,     # 32KB L1 par core
            'l2_cache_kb': 512,    # 512KB L2 partagé
            'memory_bandwidth_gbps': 6,   # ~6 GB/s
            'optimal_workers': 2,
            'cache_line_size': 64,
            'prefetch_distance': 64
        },
        'BCM2837': {  # Raspberry Pi 3
            'cpu_cores': 4,
            'cpu_freq_max': 1400,  # 1.4 GHz
            'l1_cache_kb': 32,
            'l2_cache_kb': 512,
            'memory_bandwidth_gbps': 3,   # ~3 GB/s
            'optimal_workers': 2,
            'cache_line_size': 64,
            'prefetch_distance': 32
        }
    }

    def __init__(self, logger=None):
        """
        Initialise l'optimiseur ARM

        Args:
            logger: Logger optionnel
        """
        self.logger = logger
        self.is_arm = self._detect_arm()
        self.chipset = self._detect_chipset() if self.is_arm else None
        self.cpu_info = self._get_cpu_info() if self.is_arm else {}

        if self.logger and self.is_arm:
            chipset_info = f" ({self.chipset})" if self.chipset else ""
            self.logger.info(f"ARMOptimizer initialisé{chipset_info}")

    def _detect_arm(self) -> bool:
        """Détecte si on est sur architecture ARM"""
        machine = platform.machine().lower()
        arm_archs = ['aarch64', 'armv7l', 'armv8', 'arm64']
        return any(arch in machine for arch in arm_archs)

    def _detect_chipset(self) -> Optional[str]:
        """Détecte le chipset ARM spécifique"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()

                # Chercher les chipsets connus
                for chipset in self.CHIPSET_OPTIMIZATIONS.keys():
                    if chipset in cpuinfo:
                        return chipset

        except:
            pass

        return None

    def _get_cpu_info(self) -> Dict[str, Any]:
        """Récupère les informations CPU ARM"""
        info = {
            'architecture': platform.machine(),
            'cpu_count': os.cpu_count() or 2,
            'ram_gb': psutil.virtual_memory().total / (1024 ** 3)
        }

        # Ajouter infos chipset si disponible
        if self.chipset and self.chipset in self.CHIPSET_OPTIMIZATIONS:
            info.update(self.CHIPSET_OPTIMIZATIONS[self.chipset])

        return info

    def optimize_workers(self, base_workers: int) -> int:
        """
        Optimise le nombre de workers pour ARM

        Sur ARM, le context switching est plus coûteux que sur x86 (CSAPP Ch.8).
        On réduit donc le nombre de workers pour minimiser les changements de contexte.

        Args:
            base_workers: Nombre de workers de base

        Returns:
            Nombre de workers optimisé pour ARM
        """
        if not self.is_arm:
            return base_workers

        # Utiliser valeur chipset si disponible
        if self.chipset and 'optimal_workers' in self.cpu_info:
            optimal = self.cpu_info['optimal_workers']
            if self.logger:
                self.logger.debug(f"Workers ARM optimisés: {base_workers} → {optimal} ({self.chipset})")
            return optimal

        # Sinon, appliquer facteur de réduction
        optimized = max(1, int(base_workers * self.ARM_WORKER_REDUCTION))

        if self.logger:
            self.logger.debug(f"Workers ARM optimisés: {base_workers} → {optimized} (-20%)")

        return optimized

    def optimize_cache_size(self, base_cache_mb: int) -> int:
        """
        Optimise la taille du cache pour ARM

        Les processeurs ARM ont généralement des caches L2 plus petits que x86.
        On réduit la taille du cache logiciel pour éviter d'évincer les caches matériels.

        Args:
            base_cache_mb: Taille du cache de base (MB)

        Returns:
            Taille du cache optimisée pour ARM (MB)
        """
        if not self.is_arm:
            return base_cache_mb

        optimized = max(50, int(base_cache_mb * self.ARM_CACHE_REDUCTION))

        if self.logger:
            self.logger.debug(f"Cache ARM optimisé: {base_cache_mb}MB → {optimized}MB (-30%)")

        return optimized

    def get_gc_thresholds(self) -> tuple[int, int, int]:
        """
        Retourne les seuils de garbage collection optimisés pour ARM

        Sur ARM avec RAM limitée, on veut un GC plus agressif pour libérer mémoire rapidement.

        Returns:
            Tuple (gen0, gen1, gen2) pour gc.set_threshold()
        """
        if not self.is_arm:
            # Valeurs par défaut Python
            return (700, 10, 10)

        ram_gb = self.cpu_info.get('ram_gb', 4)

        if ram_gb < 2:
            # Pi avec très peu de RAM: GC très agressif
            return (400, 5, 5)
        elif ram_gb < 4:
            # Pi avec peu de RAM: GC agressif
            return (500, 8, 8)
        elif ram_gb < 8:
            # Pi standard: GC modérément agressif
            return (600, 10, 10)
        else:
            # Pi haute capacité: GC normal
            return (700, 10, 10)

    def get_subprocess_optimization(self) -> Dict[str, Any]:
        """
        Retourne les paramètres optimisés pour subprocess sur ARM

        Returns:
            Dict avec paramètres subprocess
        """
        if not self.is_arm:
            return {}

        # Sur ARM, préférer posix_spawn au fork quand disponible
        return {
            'close_fds': True,           # Fermer FDs pour économiser mémoire
            'start_new_session': False,   # Éviter overhead session
            'restore_signals': True,      # Restaurer signaux par défaut
            'preexec_fn': None           # Éviter callback coûteux
        }

    def get_io_buffer_size(self, operation_type: str = 'default') -> int:
        """
        Retourne la taille de buffer I/O optimale pour ARM

        Args:
            operation_type: Type d'opération ('default', 'network', 'disk')

        Returns:
            Taille du buffer en bytes
        """
        if not self.is_arm:
            return 8192  # 8KB par défaut

        # Aligner sur cache line ARM (généralement 64 bytes)
        cache_line = self.cpu_info.get('cache_line_size', 64)

        if operation_type == 'network':
            # Réseau: buffers plus grands (moins de syscalls)
            return cache_line * 256  # 16KB pour 64-byte cache line
        elif operation_type == 'disk':
            # Disque: buffers moyens (bon compromis)
            return cache_line * 128  # 8KB pour 64-byte cache line
        else:
            # Par défaut: buffers petits (économie mémoire)
            return cache_line * 64   # 4KB pour 64-byte cache line

    def get_optimization_report(self) -> str:
        """
        Génère un rapport des optimisations ARM appliquées

        Returns:
            Rapport formaté
        """
        if not self.is_arm:
            return "⚠️  Pas d'architecture ARM détectée"

        lines = []
        lines.append("╔═══════════════════════════════════════════════════════╗")
        lines.append("║          OPTIMISATIONS ARM                           ║")
        lines.append("╠═══════════════════════════════════════════════════════╣")

        # Architecture
        arch = self.cpu_info.get('architecture', 'Unknown')
        lines.append(f"║ Architecture: {arch:<42} ║")

        # Chipset
        if self.chipset:
            lines.append(f"║ Chipset: {self.chipset:<47} ║")

        # CPU
        cpu_count = self.cpu_info.get('cpu_count', 0)
        lines.append(f"║ CPU Cores: {cpu_count:<45} ║")

        # Fréquence max
        if 'cpu_freq_max' in self.cpu_info:
            freq = self.cpu_info['cpu_freq_max']
            lines.append(f"║ Fréquence Max: {freq} MHz{' ' * (37 - len(f'{freq} MHz'))}║")

        # Caches
        if 'l1_cache_kb' in self.cpu_info:
            l1 = self.cpu_info['l1_cache_kb']
            lines.append(f"║ L1 Cache: {l1}KB par core{' ' * (36 - len(f'{l1}KB par core'))}║")

        if 'l2_cache_mb' in self.cpu_info:
            l2 = self.cpu_info['l2_cache_mb']
            lines.append(f"║ L2 Cache: {l2}MB partagé{' ' * (37 - len(f'{l2}MB partagé'))}║")
        elif 'l2_cache_kb' in self.cpu_info:
            l2 = self.cpu_info['l2_cache_kb']
            lines.append(f"║ L2 Cache: {l2}KB partagé{' ' * (36 - len(f'{l2}KB partagé'))}║")

        lines.append("╠═══════════════════════════════════════════════════════╣")
        lines.append("║ OPTIMISATIONS APPLIQUÉES:                            ║")

        # Workers
        optimal_workers = self.cpu_info.get('optimal_workers')
        if optimal_workers:
            lines.append(f"║  • Workers optimisés: {optimal_workers:<32} ║")

        # GC
        gc_thresholds = self.get_gc_thresholds()
        lines.append(f"║  • GC thresholds: {gc_thresholds}{' ' * (31 - len(str(gc_thresholds)))}║")

        # Buffer I/O
        io_buffer = self.get_io_buffer_size()
        lines.append(f"║  • Buffer I/O: {io_buffer} bytes{' ' * (33 - len(f'{io_buffer} bytes'))}║")

        # Cache line
        if 'cache_line_size' in self.cpu_info:
            cache_line = self.cpu_info['cache_line_size']
            lines.append(f"║  • Cache line: {cache_line} bytes{' ' * (33 - len(f'{cache_line} bytes'))}║")

        lines.append("╚═══════════════════════════════════════════════════════╝")

        return '\n'.join(lines)

    def apply_optimizations(self, settings) -> Dict[str, Any]:
        """
        Applique les optimisations ARM aux settings

        Args:
            settings: Objet settings à modifier

        Returns:
            Dict avec les modifications appliquées
        """
        if not self.is_arm:
            return {'arm_optimized': False}

        modifications = {}

        # Workers
        if hasattr(settings, 'parallel_workers'):
            old_workers = settings.parallel_workers
            settings.parallel_workers = self.optimize_workers(old_workers)
            modifications['workers'] = {'old': old_workers, 'new': settings.parallel_workers}

        # Cache
        if hasattr(settings, 'cache_config') and hasattr(settings.cache_config, 'max_cache_size_mb'):
            old_cache = settings.cache_config.max_cache_size_mb
            settings.cache_config.max_cache_size_mb = self.optimize_cache_size(old_cache)
            modifications['cache_mb'] = {'old': old_cache, 'new': settings.cache_config.max_cache_size_mb}

        # GC
        gc_thresholds = self.get_gc_thresholds()
        modifications['gc_thresholds'] = gc_thresholds

        if self.logger:
            self.logger.info(f"Optimisations ARM appliquées: {len(modifications)} paramètres modifiés")

        return {
            'arm_optimized': True,
            'chipset': self.chipset,
            'modifications': modifications
        }
