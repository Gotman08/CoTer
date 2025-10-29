"""Optimiseur hardware pour adapter les paramètres au Raspberry Pi et autres systèmes"""

import platform
import os
from typing import Dict, Any
import psutil

class HardwareOptimizer:
    """Détecte le hardware et optimise les paramètres en conséquence"""

    def __init__(self, logger=None):
        """
        Initialise l'optimiseur hardware

        Args:
            logger: Logger pour les messages
        """
        self.logger = logger
        self.hardware_info = self._detect_hardware()

        if self.logger:
            self.logger.info(f"Hardware détecté: {self.hardware_info['device_type']}")
            self.logger.info(f"RAM: {self.hardware_info['ram_gb']:.1f} GB")
            self.logger.info(f"CPU: {self.hardware_info['cpu_count']} cores")

    def _detect_hardware(self) -> Dict[str, Any]:
        """
        Détecte les caractéristiques du hardware

        Returns:
            Dict avec les informations hardware
        """
        # Informations système
        system = platform.system()
        machine = platform.machine()
        processor = platform.processor()

        # RAM
        ram_bytes = psutil.virtual_memory().total
        ram_gb = ram_bytes / (1024 ** 3)

        # CPU
        cpu_count = os.cpu_count() or 2
        cpu_freq = psutil.cpu_freq()

        # Détection Raspberry Pi
        is_raspberry_pi = self._is_raspberry_pi()

        # Type de device
        if is_raspberry_pi:
            device_type = self._get_raspberry_pi_model(ram_gb)
        elif ram_gb < 4:
            device_type = "low_end"
        elif ram_gb < 8:
            device_type = "mid_range"
        else:
            device_type = "high_end"

        return {
            'system': system,
            'machine': machine,
            'processor': processor,
            'ram_gb': ram_gb,
            'ram_bytes': ram_bytes,
            'cpu_count': cpu_count,
            'cpu_freq_mhz': cpu_freq.current if cpu_freq else 0,
            'is_raspberry_pi': is_raspberry_pi,
            'device_type': device_type
        }

    def _is_raspberry_pi(self) -> bool:
        """
        Détecte si on est sur un Raspberry Pi

        Returns:
            True si Raspberry Pi
        """
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                return 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo
        except:
            return False

    def _get_raspberry_pi_model(self, ram_gb: float) -> str:
        """
        Détermine le modèle de Raspberry Pi

        Args:
            ram_gb: RAM disponible

        Returns:
            Modèle approximatif
        """
        if ram_gb >= 7:  # ~8GB
            return "raspberry_pi_5_8gb"
        elif ram_gb >= 3.5:  # ~4GB
            return "raspberry_pi_5_4gb"
        elif ram_gb >= 1.5:  # ~2GB
            return "raspberry_pi_4_2gb"
        else:
            return "raspberry_pi_old"

    def get_optimized_params(self) -> Dict[str, Any]:
        """
        Retourne des paramètres optimisés selon le hardware

        Returns:
            Dict avec les paramètres recommandés
        """
        device_type = self.hardware_info['device_type']
        ram_gb = self.hardware_info['ram_gb']
        cpu_count = self.hardware_info['cpu_count']

        # Paramètres par défaut
        params = {
            'ollama_timeout': 120,
            'agent_max_steps': 50,
            'parallel_workers': 2,
            'cache_size_mb': 500,
            'cache_enabled': True,
            'swap_recommended': False,
            'low_memory_mode': False
        }

        # Ajustements selon le device
        if device_type == "raspberry_pi_5_8gb":
            params.update({
                'ollama_timeout': 90,
                'agent_max_steps': 50,
                'parallel_workers': min(4, cpu_count),
                'cache_size_mb': 1000,
                'low_memory_mode': False
            })

        elif device_type == "raspberry_pi_5_4gb":
            params.update({
                'ollama_timeout': 120,
                'agent_max_steps': 40,
                'parallel_workers': min(3, cpu_count),
                'cache_size_mb': 500,
                'low_memory_mode': False
            })

        elif device_type.startswith("raspberry_pi"):
            # Raspberry Pi plus ancien ou avec moins de RAM
            params.update({
                'ollama_timeout': 180,
                'agent_max_steps': 30,
                'parallel_workers': 2,
                'cache_size_mb': 200,
                'swap_recommended': True,
                'low_memory_mode': True
            })

        elif device_type == "low_end":
            params.update({
                'ollama_timeout': 150,
                'agent_max_steps': 40,
                'parallel_workers': 2,
                'cache_size_mb': 300,
                'low_memory_mode': True
            })

        elif device_type == "mid_range":
            params.update({
                'ollama_timeout': 120,
                'agent_max_steps': 50,
                'parallel_workers': min(4, cpu_count),
                'cache_size_mb': 800,
                'low_memory_mode': False
            })

        else:  # high_end
            params.update({
                'ollama_timeout': 90,
                'agent_max_steps': 100,
                'parallel_workers': min(8, cpu_count),
                'cache_size_mb': 2000,
                'low_memory_mode': False
            })

        return params

    def get_memory_status(self) -> Dict[str, Any]:
        """
        Retourne l'état actuel de la mémoire

        Returns:
            Dict avec les informations mémoire
        """
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            'ram_total_gb': round(mem.total / (1024 ** 3), 2),
            'ram_available_gb': round(mem.available / (1024 ** 3), 2),
            'ram_used_gb': round(mem.used / (1024 ** 3), 2),
            'ram_percent': mem.percent,
            'swap_total_gb': round(swap.total / (1024 ** 3), 2),
            'swap_used_gb': round(swap.used / (1024 ** 3), 2),
            'swap_percent': swap.percent
        }

    def check_memory_pressure(self) -> Dict[str, Any]:
        """
        Vérifie si le système est sous pression mémoire

        Returns:
            Dict avec l'état et des recommandations
        """
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        pressure_level = "normal"
        recommendations = []

        if mem.percent > 90:
            pressure_level = "critical"
            recommendations.append("RAM critique! Fermez des applications.")
            recommendations.append("Considérez augmenter le swap.")

        elif mem.percent > 75:
            pressure_level = "high"
            recommendations.append("RAM élevée. Mode low-memory recommandé.")
            if swap.percent > 50:
                recommendations.append("Swap utilisé. Performances réduites attendues.")

        elif mem.percent > 60:
            pressure_level = "moderate"
            if swap.percent > 25:
                recommendations.append("Swap utilisé. Considérez libérer de la RAM.")

        return {
            'pressure_level': pressure_level,
            'ram_percent': mem.percent,
            'swap_percent': swap.percent,
            'recommendations': recommendations,
            'should_enable_low_memory': pressure_level in ['high', 'critical']
        }

    def suggest_swap_size(self) -> int:
        """
        Suggère une taille de swap appropriée

        Returns:
            Taille de swap recommandée en MB
        """
        ram_gb = self.hardware_info['ram_gb']

        if ram_gb < 2:
            return 4096  # 4 GB
        elif ram_gb < 4:
            return 2048  # 2 GB
        elif ram_gb < 8:
            return 1024  # 1 GB
        else:
            return 512   # 512 MB (juste en cas)

    def get_cpu_status(self) -> Dict[str, Any]:
        """
        Retourne l'état du CPU

        Returns:
            Dict avec les informations CPU
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()

        return {
            'cpu_percent_avg': cpu_percent,
            'cpu_per_core': cpu_per_core,
            'cpu_count': self.hardware_info['cpu_count'],
            'cpu_freq_current': cpu_freq.current if cpu_freq else 0,
            'cpu_freq_min': cpu_freq.min if cpu_freq else 0,
            'cpu_freq_max': cpu_freq.max if cpu_freq else 0
        }

    def get_optimization_report(self) -> str:
        """
        Génère un rapport d'optimisation complet

        Returns:
            Rapport formaté en texte
        """
        params = self.get_optimized_params()
        mem_status = self.get_memory_status()
        pressure = self.check_memory_pressure()

        report = []
        report.append("╔═══════════════════════════════════════════════════════╗")
        report.append("║          RAPPORT D'OPTIMISATION HARDWARE             ║")
        report.append("╠═══════════════════════════════════════════════════════╣")
        report.append(f"║ Device: {self.hardware_info['device_type']:<44} ║")
        report.append(f"║ RAM: {mem_status['ram_total_gb']:.1f} GB ({mem_status['ram_percent']:.0f}% utilisée){' '*(29-len(f'{mem_status['ram_total_gb']:.1f} GB ({mem_status['ram_percent']:.0f}% utilisée)'))}║")
        report.append(f"║ CPU: {self.hardware_info['cpu_count']} cores{' '*(44-len(f'{self.hardware_info['cpu_count']} cores'))}║")
        report.append("╠═══════════════════════════════════════════════════════╣")
        report.append("║ PARAMÈTRES OPTIMISÉS:                                ║")
        report.append(f"║  • Workers parallèles: {params['parallel_workers']:<30} ║")
        report.append(f"║  • Taille cache: {params['cache_size_mb']} MB{' '*(32-len(f'{params['cache_size_mb']} MB'))}║")
        report.append(f"║  • Timeout Ollama: {params['ollama_timeout']}s{' '*(32-len(f'{params['ollama_timeout']}s'))}║")
        report.append(f"║  • Max étapes agent: {params['agent_max_steps']:<30} ║")

        if pressure['recommendations']:
            report.append("╠═══════════════════════════════════════════════════════╣")
            report.append(f"║ ⚠️  PRESSION MÉMOIRE: {pressure['pressure_level'].upper():<30} ║")
            for rec in pressure['recommendations']:
                report.append(f"║  • {rec:<48} ║")

        report.append("╚═══════════════════════════════════════════════════════╝")

        return '\n'.join(report)

    def apply_optimizations(self, settings):
        """
        Applique les optimisations au settings

        Args:
            settings: Objet Settings à modifier
        """
        params = self.get_optimized_params()

        # Appliquer les paramètres optimisés
        settings.ollama_timeout = params['ollama_timeout']
        settings.agent_max_steps = params['agent_max_steps']

        # Paramètres de cache
        if hasattr(settings, 'cache_config'):
            settings.cache_config.max_cache_size_mb = params['cache_size_mb']

        if self.logger:
            self.logger.info("Optimisations hardware appliquées")
            if params['swap_recommended']:
                self.logger.warning(f"⚠️  Swap recommandé: {self.suggest_swap_size()} MB")
            if params['low_memory_mode']:
                self.logger.warning("⚠️  Mode low-memory activé")
