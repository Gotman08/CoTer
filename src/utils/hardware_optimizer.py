"""Optimiseur hardware pour adapter les paramètres au Raspberry Pi et autres systèmes"""

import platform
import os
from typing import Dict, Any, Optional
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

        # Détection architecture ARM
        is_arm = self._is_arm_architecture(machine)

        # Détection Raspberry Pi et chipset spécifique
        is_raspberry_pi, pi_chipset = self._is_raspberry_pi()

        # Type de device
        if is_raspberry_pi:
            device_type = self._get_raspberry_pi_model(ram_gb, pi_chipset, cpu_freq)
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
            'is_arm': is_arm,
            'ram_gb': ram_gb,
            'ram_bytes': ram_bytes,
            'cpu_count': cpu_count,
            'cpu_freq_mhz': cpu_freq.current if cpu_freq else 0,
            'cpu_freq_max': cpu_freq.max if cpu_freq else 0,
            'is_raspberry_pi': is_raspberry_pi,
            'pi_chipset': pi_chipset,
            'device_type': device_type
        }

    def _is_arm_architecture(self, machine: str) -> bool:
        """
        Détecte si on est sur architecture ARM

        Args:
            machine: Architecture machine (ex: aarch64, armv7l)

        Returns:
            True si ARM
        """
        arm_archs = ['aarch64', 'armv7l', 'armv8', 'arm64']
        return any(arch in machine.lower() for arch in arm_archs)

    def _is_raspberry_pi(self) -> tuple[bool, str]:
        """
        Détecte si on est sur un Raspberry Pi et identifie le chipset

        Returns:
            Tuple (is_pi, chipset) - chipset est '' si pas un Pi
        """
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()

                # Identifier le chipset spécifique
                if 'BCM2712' in cpuinfo:
                    return (True, 'BCM2712')  # Raspberry Pi 5
                elif 'BCM2711' in cpuinfo:
                    return (True, 'BCM2711')  # Raspberry Pi 4
                elif 'BCM2837' in cpuinfo:
                    return (True, 'BCM2837')  # Raspberry Pi 3
                elif 'BCM2836' in cpuinfo:
                    return (True, 'BCM2836')  # Raspberry Pi 2
                elif 'BCM2835' in cpuinfo:
                    return (True, 'BCM2835')  # Raspberry Pi 1/Zero
                elif 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo:
                    return (True, 'BCM_UNKNOWN')

                return (False, '')
        except:
            return (False, '')

    def _get_raspberry_pi_model(self, ram_gb: float, chipset: str = '', cpu_freq=None) -> str:
        """
        Détermine le modèle exact de Raspberry Pi

        Args:
            ram_gb: RAM disponible
            chipset: Chipset détecté (BCM2712, BCM2711, etc.)
            cpu_freq: Informations fréquence CPU

        Returns:
            Modèle exact du Raspberry Pi
        """
        # Pi 5 - BCM2712 avec CPU jusqu'à 2.4 GHz
        if chipset == 'BCM2712':
            if ram_gb >= 7:  # ~8GB
                return "raspberry_pi_5_8gb"
            else:  # ~4GB
                return "raspberry_pi_5_4gb"

        # Pi 4 - BCM2711 avec CPU jusqu'à 1.8 GHz
        elif chipset == 'BCM2711':
            if ram_gb >= 7:  # ~8GB
                return "raspberry_pi_4_8gb"
            elif ram_gb >= 3.5:  # ~4GB
                return "raspberry_pi_4_4gb"
            elif ram_gb >= 1.5:  # ~2GB
                return "raspberry_pi_4_2gb"
            else:  # ~1GB
                return "raspberry_pi_4_1gb"

        # Pi 3 - BCM2837
        elif chipset == 'BCM2837':
            return "raspberry_pi_3"

        # Pi 2 - BCM2836
        elif chipset == 'BCM2836':
            return "raspberry_pi_2"

        # Pi 1/Zero - BCM2835
        elif chipset == 'BCM2835':
            return "raspberry_pi_old"

        # Fallback sur détection par RAM (ancienne méthode)
        else:
            if ram_gb >= 7:
                return "raspberry_pi_5_8gb"
            elif ram_gb >= 3.5:
                return "raspberry_pi_4_4gb"
            elif ram_gb >= 1.5:
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
            # Pi 5 8GB: Performances optimales
            # ARM: Réduire workers de 20% (context switch coûteux)
            optimal_workers = 3 if self.hardware_info.get('is_arm') else 4
            params.update({
                'ollama_timeout': 90,
                'agent_max_steps': 50,
                'parallel_workers': min(optimal_workers, cpu_count),
                'cache_size_mb': 400,  # Réduit pour SD card (était 1000)
                'cache_location': 'tmpfs',  # Préférer RAM si disponible
                'low_memory_mode': False,
                'use_compression': True,  # Compression zlib rapide sur ARM
                'gc_threshold': (700, 10, 10)  # GC moins agressif
            })

        elif device_type == "raspberry_pi_5_4gb":
            # Pi 5 4GB: Équilibre performance/mémoire
            optimal_workers = 2 if self.hardware_info.get('is_arm') else 3
            params.update({
                'ollama_timeout': 120,
                'agent_max_steps': 40,
                'parallel_workers': min(optimal_workers, cpu_count),
                'cache_size_mb': 200,  # Réduit pour SD card (était 500)
                'cache_location': 'tmpfs',  # Préférer RAM si disponible
                'low_memory_mode': False,
                'use_compression': True,  # Compression pour économiser RAM
                'gc_threshold': (500, 10, 10)  # GC plus agressif
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

    def get_cpu_temperature(self) -> Optional[float]:
        """
        Retourne la température du CPU en degrés Celsius

        Returns:
            Température en °C ou None si non disponible
        """
        try:
            # Linux: lire depuis /sys/class/thermal/
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_milli = int(f.read().strip())
                return temp_milli / 1000.0
        except:
            # Essayer via psutil (si sensors disponibles)
            try:
                temps = psutil.sensors_temperatures()
                if 'cpu_thermal' in temps:
                    return temps['cpu_thermal'][0].current
                elif 'coretemp' in temps:
                    return temps['coretemp'][0].current
            except:
                pass

        return None

    def check_thermal_throttling(self) -> Dict[str, Any]:
        """
        Vérifie si le CPU est en throttling thermique

        Returns:
            Dict avec état thermique et recommandations
        """
        temp = self.get_cpu_temperature()

        if temp is None:
            return {
                'available': False,
                'temperature': None,
                'throttling': False,
                'status': 'unknown',
                'recommendations': []
            }

        # Déterminer l'état thermique
        if temp > 85:
            status = 'critical'
            throttling = True
            recommendations = [
                "Température critique! Arrêtez les tâches lourdes.",
                "Vérifiez le refroidissement (ventilateur, dissipateur).",
                "Réduisez le nombre de workers parallèles."
            ]
        elif temp > 80:
            status = 'high'
            throttling = True
            recommendations = [
                "Température élevée. Throttling actif.",
                "Réduisez la charge ou améliorez le refroidissement."
            ]
        elif temp > 70:
            status = 'warm'
            throttling = False
            recommendations = [
                "Température en hausse. Surveillez la charge."
            ]
        elif temp > 60:
            status = 'normal_warm'
            throttling = False
            recommendations = []
        else:
            status = 'normal'
            throttling = False
            recommendations = []

        return {
            'available': True,
            'temperature': round(temp, 1),
            'throttling': throttling,
            'status': status,
            'recommendations': recommendations
        }

    def get_cpu_status(self) -> Dict[str, Any]:
        """
        Retourne l'état complet du CPU (charge + température)

        Returns:
            Dict avec les informations CPU
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        thermal = self.check_thermal_throttling()

        return {
            'cpu_percent_avg': cpu_percent,
            'cpu_per_core': cpu_per_core,
            'cpu_count': self.hardware_info['cpu_count'],
            'cpu_freq_current': cpu_freq.current if cpu_freq else 0,
            'cpu_freq_min': cpu_freq.min if cpu_freq else 0,
            'cpu_freq_max': cpu_freq.max if cpu_freq else 0,
            'temperature': thermal['temperature'],
            'thermal_throttling': thermal['throttling'],
            'thermal_status': thermal['status']
        }

    def get_optimization_report_dict(self) -> Dict[str, Any]:
        """
        Génère un rapport d'optimisation sous forme de dictionnaire
        (pour affichage avec Rich)

        Returns:
            Dictionnaire avec les informations hardware et optimisations
        """
        params = self.get_optimized_params()
        mem_status = self.get_memory_status()
        thermal = self.check_thermal_throttling()

        # Informations de base
        device = self.hardware_info['device_type'].replace('_', ' ').title()

        # Ajouter chipset si Raspberry Pi
        if self.hardware_info['is_raspberry_pi']:
            chipset = self.hardware_info.get('pi_chipset', 'Unknown')
            device = f"{device} ({chipset})"

        # Format RAM
        ram_info = f"{mem_status['ram_total_gb']:.1f} GB ({mem_status['ram_percent']:.0f}% utilisée)"

        # Format CPU
        cpu_info = f"{self.hardware_info['cpu_count']} cores"
        if self.hardware_info.get('cpu_freq_max'):
            cpu_info += f" @ {self.hardware_info['cpu_freq_max']:.0f} MHz"

        # Température si disponible
        temp_info = None
        if thermal['available']:
            temp = thermal['temperature']
            status = thermal['status']
            temp_info = f"{temp}°C ({status})"

        # Construction du dictionnaire
        report = {
            'device': device,
            'ram': ram_info,
            'cpu': cpu_info,
            'workers': params['parallel_workers'],
            'cache_size': f"{params['cache_size_mb']} MB",
            'timeout': f"{params['ollama_timeout']}s",
            'max_steps': params['agent_max_steps']
        }

        # Ajouter température si disponible
        if temp_info:
            report['temperature'] = temp_info

        return report

    def get_optimization_report(self) -> str:
        """
        Génère un rapport d'optimisation complet

        Returns:
            Rapport formaté en texte
        """
        params = self.get_optimized_params()
        mem_status = self.get_memory_status()
        pressure = self.check_memory_pressure()
        thermal = self.check_thermal_throttling()

        report = []
        report.append("╔═══════════════════════════════════════════════════════╗")
        report.append("║          RAPPORT D'OPTIMISATION HARDWARE             ║")
        report.append("╠═══════════════════════════════════════════════════════╣")
        report.append(f"║ Device: {self.hardware_info['device_type']:<44} ║")

        # Info chipset pour Raspberry Pi
        if self.hardware_info['is_raspberry_pi']:
            chipset = self.hardware_info.get('pi_chipset', 'Unknown')
            report.append(f"║ Chipset: {chipset:<45} ║")

        # Info architecture
        if self.hardware_info.get('is_arm'):
            arch = self.hardware_info['machine']
            report.append(f"║ Architecture: ARM ({arch}){' '*(33-len(f'ARM ({arch})'))}║")

        report.append(f"║ RAM: {mem_status['ram_total_gb']:.1f} GB ({mem_status['ram_percent']:.0f}% utilisée){' '*(29-len(f'{mem_status['ram_total_gb']:.1f} GB ({mem_status['ram_percent']:.0f}% utilisée)'))}║")
        report.append(f"║ CPU: {self.hardware_info['cpu_count']} cores{' '*(44-len(f'{self.hardware_info['cpu_count']} cores'))}║")

        # Info thermique
        if thermal['available']:
            temp = thermal['temperature']
            status = thermal['status']
            temp_icon = "🟢" if temp < 70 else "🟡" if temp < 80 else "🔴"
            report.append(f"║ Température: {temp_icon} {temp}°C ({status}){' '*(34-len(f'{temp}°C ({status})'))}║")

        report.append("╠═══════════════════════════════════════════════════════╣")
        report.append("║ PARAMÈTRES OPTIMISÉS:                                ║")
        report.append(f"║  • Workers parallèles: {params['parallel_workers']:<30} ║")
        report.append(f"║  • Taille cache: {params['cache_size_mb']} MB{' '*(32-len(f'{params['cache_size_mb']} MB'))}║")
        report.append(f"║  • Timeout Ollama: {params['ollama_timeout']}s{' '*(32-len(f'{params['ollama_timeout']}s'))}║")
        report.append(f"║  • Max étapes agent: {params['agent_max_steps']:<30} ║")

        # Alertes thermiques
        if thermal['throttling']:
            report.append("╠═══════════════════════════════════════════════════════╣")
            report.append("║ ⚠️  ALERTE THERMIQUE: THROTTLING ACTIF              ║")
            for rec in thermal['recommendations']:
                # Tronquer si trop long
                rec_short = rec[:48] if len(rec) > 48 else rec
                report.append(f"║  • {rec_short:<48} ║")

        # Pression mémoire
        if pressure['recommendations']:
            report.append("╠═══════════════════════════════════════════════════════╣")
            report.append(f"║ ⚠️  PRESSION MÉMOIRE: {pressure['pressure_level'].upper():<30} ║")
            for rec in pressure['recommendations']:
                rec_short = rec[:48] if len(rec) > 48 else rec
                report.append(f"║  • {rec_short:<48} ║")

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
