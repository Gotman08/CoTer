"""
Ollama Server Manager
Gère le démarrage automatique et la détection du serveur Ollama
"""

import subprocess
import time
import platform
import psutil
import requests
from typing import Tuple, Optional


class OllamaManager:
    """Gestionnaire du serveur Ollama pour démarrage automatique"""

    def __init__(self, host: str = "http://localhost:11434", logger=None):
        """
        Initialise le gestionnaire Ollama

        Args:
            host: URL du serveur Ollama
            logger: Logger pour les messages
        """
        self.host = host.rstrip('/')
        self.logger = logger

        # Extraire le port de l'URL (défaut 11434)
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.host)
            self.port = parsed.port or 11434
        except Exception:
            self.port = 11434

    def is_server_running(self) -> Tuple[bool, str]:
        """
        Vérifie si le serveur Ollama est en cours d'exécution

        Utilise une détection multicouche:
        1. Test API (principal): requête HTTP à /api/tags
        2. Test port (secondaire): vérification si port 11434 est bound
        3. Test process (tertiaire): recherche du process "ollama"

        Returns:
            Tuple (is_running, message)
        """
        # Test 1: API (le plus fiable)
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=2)
            if response.status_code == 200:
                return True, "Ollama serve est déjà en cours d'exécution"
        except requests.exceptions.ConnectionError:
            # Serveur pas accessible, continuer avec autres tests
            pass
        except requests.exceptions.Timeout:
            # Timeout, probablement pas en cours
            pass
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Erreur test API Ollama: {e}")

        # Test 2: Port (utile pour diagnostic)
        if self._check_port_in_use():
            # Port utilisé mais API ne répond pas
            return False, f"Le port {self.port} est utilisé mais Ollama ne répond pas"

        # Test 3: Process (diagnostic supplémentaire)
        if self._check_process_running():
            # Process existe mais ne répond pas
            return False, "Process Ollama détecté mais ne répond pas à l'API"

        # Aucun signe du serveur
        return False, "Ollama serve n'est pas en cours d'exécution"

    def start_server(self, timeout: int = 10) -> Tuple[bool, str]:
        """
        Démarre le serveur Ollama en arrière-plan

        Args:
            timeout: Temps d'attente max pour que le serveur réponde (secondes)

        Returns:
            Tuple (success, message)
        """
        if self.logger:
            self.logger.info("Tentative de démarrage du serveur Ollama...")

        # Vérifier si Ollama est installé
        if not self.is_ollama_installed():
            return False, (
                "Ollama n'est pas installé\n"
                "\n"
                "💡 Pour installer Ollama:\n"
                "   1. Visitez https://ollama.ai\n"
                "   2. Téléchargez pour votre système\n"
                "   3. Suivez les instructions d'installation\n"
                "   4. Relancez Terminal IA"
            )

        try:
            # Démarrer le serveur en arrière-plan
            if platform.system() == "Windows":
                # Windows: masquer la fenêtre console
                process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Linux/Mac/WSL: détacher du processus parent
                process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )

            if self.logger:
                self.logger.info(f"Process Ollama démarré (PID: {process.pid})")

            # Attendre que le serveur réponde
            if self._wait_for_server(timeout):
                return True, "Ollama serve démarré avec succès"
            else:
                return False, (
                    f"Ollama serve a démarré mais ne répond pas après {timeout}s\n"
                    "\n"
                    "💡 Vérifications suggérées:\n"
                    f"   1. Vérifiez les logs: ~/.ollama/logs/\n"
                    "   2. Vérifiez que le port {self.port} n'est pas bloqué\n"
                    "   3. Essayez de lancer manuellement: ollama serve"
                )

        except FileNotFoundError:
            return False, (
                "Commande 'ollama' introuvable\n"
                "\n"
                "💡 Ollama n'est peut-être pas dans votre PATH:\n"
                "   1. Vérifiez l'installation: which ollama\n"
                "   2. Réinstallez si nécessaire: https://ollama.ai"
            )

        except PermissionError:
            return False, (
                "Permission refusée pour démarrer Ollama\n"
                "\n"
                "💡 Solutions possibles:\n"
                f"   1. Vérifiez les permissions sur le port {self.port}\n"
                "   2. Essayez avec les privilèges appropriés\n"
                "   3. Vérifiez les permissions du binaire ollama"
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur démarrage Ollama: {e}", exc_info=True)
            return False, f"Erreur inattendue lors du démarrage: {str(e)}"

    def ensure_server_running(self) -> Tuple[bool, str]:
        """
        Garantit que le serveur Ollama est en cours d'exécution

        Vérifie d'abord si le serveur tourne, sinon tente de le démarrer.
        C'est la méthode principale à appeler au démarrage de l'application.

        Returns:
            Tuple (success, message)
        """
        # Étape 1: Vérifier si déjà en cours
        is_running, check_message = self.is_server_running()

        if is_running:
            if self.logger:
                self.logger.info("Serveur Ollama déjà actif")
            return True, check_message

        # Étape 2: Pas en cours, afficher le statut
        if self.logger:
            self.logger.info(check_message)

        print(f"⏳ {check_message}...")
        print("🚀 Démarrage de Ollama serve...")

        # Étape 3: Tenter de démarrer
        success, start_message = self.start_server()

        if success and self.logger:
            self.logger.info("Serveur Ollama démarré avec succès")

        return success, start_message

    def is_ollama_installed(self) -> bool:
        """
        Vérifie si le binaire Ollama est disponible dans le PATH

        Returns:
            True si Ollama est installé, False sinon
        """
        try:
            # Essayer d'exécuter 'ollama --version' pour vérifier l'installation
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def _check_port_in_use(self) -> bool:
        """
        Vérifie si le port Ollama est actuellement utilisé

        Returns:
            True si le port est bound, False sinon
        """
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == self.port and conn.status == 'LISTEN':
                    if self.logger:
                        self.logger.debug(f"Port {self.port} est utilisé")
                    return True
        except (psutil.AccessDenied, AttributeError):
            # Permission refusée ou attribut manquant, skip
            pass
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Erreur vérification port: {e}")

        return False

    def _check_process_running(self) -> bool:
        """
        Vérifie si un process Ollama est en cours d'exécution

        Returns:
            True si un process ollama est trouvé, False sinon
        """
        try:
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name']
                if proc_name and 'ollama' in proc_name.lower():
                    if self.logger:
                        self.logger.debug(f"Process Ollama trouvé: {proc_name}")
                    return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            # Permission refusée ou process terminé, skip
            pass
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Erreur vérification process: {e}")

        return False

    def _wait_for_server(self, timeout: int) -> bool:
        """
        Attend que le serveur Ollama devienne accessible

        Args:
            timeout: Temps d'attente maximum en secondes

        Returns:
            True si le serveur répond dans le délai, False sinon
        """
        start_time = time.time()
        retry_interval = 0.5  # Vérifier toutes les 0.5s

        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.host}/api/tags", timeout=1)
                if response.status_code == 200:
                    elapsed = time.time() - start_time
                    if self.logger:
                        self.logger.info(f"Serveur Ollama prêt après {elapsed:.1f}s")
                    return True
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                # Pas encore prêt, attendre
                pass
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Erreur attente serveur: {e}")

            time.sleep(retry_interval)

        # Timeout atteint
        if self.logger:
            self.logger.warning(f"Timeout atteint ({timeout}s), serveur ne répond pas")

        return False
