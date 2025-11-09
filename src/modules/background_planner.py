"""Module de planification en arrière-plan pour mode AUTO"""

import threading
import queue
import time
from typing import Optional, Callable, Dict
from datetime import datetime


class BackgroundPlanner:
    """
    Système de planification en arrière-plan qui analyse les requêtes utilisateur
    et génère des plans d'exécution sans bloquer le terminal.

    Caractéristiques:
    - Thread séparé pour éviter le blocage
    - Queue thread-safe pour les requêtes
    - Génération automatique de plans pour requêtes complexes
    - Callbacks pour notifications UI
    """

    def __init__(self, project_planner, logger=None):
        """
        Initialise le planificateur en arrière-plan

        Args:
            project_planner: Instance de ProjectPlanner à utiliser pour l'analyse
            logger: Logger optionnel pour les messages
        """
        self.planner = project_planner
        self.logger = logger

        # Queues thread-safe
        self.request_queue = queue.Queue(maxsize=10)  # Limite pour éviter surcharge
        self.result_queue = queue.Queue(maxsize=5)     # Stockage limité des résultats

        # Thread de travail
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False
        self._lock = threading.Lock()

        # Dernier plan généré
        self.latest_plan: Optional[Dict] = None
        self.latest_analysis: Optional[Dict] = None

        # Callbacks pour notifications
        self.on_planning_start: Optional[Callable] = None
        self.on_planning_complete: Optional[Callable[[Dict, Dict], None]] = None
        self.on_analysis_complete: Optional[Callable[[Dict], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

        # Statistiques
        self.stats = {
            'total_requests': 0,
            'plans_generated': 0,
            'simple_requests': 0,
            'errors': 0,
            'avg_planning_time': 0.0
        }

    def start(self):
        """Démarre le thread de planification en arrière-plan"""
        with self._lock:
            if self.is_running:
                if self.logger:
                    self.logger.warning("BackgroundPlanner déjà démarré")
                return

            self.is_running = True
            self.worker_thread = threading.Thread(
                target=self._planning_loop,
                name="BackgroundPlannerWorker",
                daemon=True  # Thread daemon pour arrêt propre
            )
            self.worker_thread.start()

            if self.logger:
                self.logger.info("BackgroundPlanner démarré")

    def stop(self):
        """Arrête proprement le thread de planification"""
        with self._lock:
            if not self.is_running:
                return

            self.is_running = False

        # Attendre que le thread se termine (timeout 2 secondes)
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)

        if self.logger:
            self.logger.info("BackgroundPlanner arrêté")

    def _planning_loop(self):
        """
        Boucle principale du thread de planification.
        Traite les requêtes de la queue et génère des plans.
        """
        while self.is_running:
            try:
                # Récupérer une requête (timeout pour permettre vérif is_running)
                try:
                    request_data = self.request_queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                user_request = request_data['request']
                request_id = request_data.get('id', 'unknown')

                if self.logger:
                    self.logger.debug(f"[BG] Traitement requête: {user_request[:50]}...")

                # Notifier début de planification
                if self.on_planning_start:
                    try:
                        self.on_planning_start()
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Erreur callback on_planning_start: {e}")

                start_time = time.time()

                # 1. Analyser la requête
                analysis = self.planner.analyze_request(user_request)
                self.latest_analysis = analysis
                self.stats['total_requests'] += 1

                if self.logger:
                    self.logger.debug(f"[BG] Analyse: {analysis}")

                # Callback analyse complète
                if self.on_analysis_complete:
                    try:
                        self.on_analysis_complete(analysis)
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Erreur callback on_analysis_complete: {e}")

                # 2. Si complexe, générer le plan
                plan = None
                if analysis.get('is_complex', False):
                    project_type = analysis.get('project_type', 'unknown')

                    if self.logger:
                        self.logger.info(f"[BG] Génération plan pour projet: {project_type}")

                    plan = self.planner.generate_project_plan(user_request, project_type)

                    # Enrichir le plan avec métadonnées
                    plan['_metadata'] = {
                        'request_id': request_id,
                        'generated_at': datetime.now().isoformat(),
                        'user_request': user_request,
                        'planning_time': time.time() - start_time
                    }

                    self.latest_plan = plan
                    self.stats['plans_generated'] += 1

                    # Stocker dans la queue de résultats
                    try:
                        self.result_queue.put_nowait({
                            'plan': plan,
                            'analysis': analysis,
                            'request_id': request_id
                        })
                    except queue.Full:
                        # Queue pleine, supprimer le plus ancien
                        try:
                            self.result_queue.get_nowait()
                            self.result_queue.put_nowait({
                                'plan': plan,
                                'analysis': analysis,
                                'request_id': request_id
                            })
                        except:
                            pass

                    if self.logger:
                        self.logger.info(f"[BG] Plan généré ({len(plan.get('steps', []))} étapes)")
                else:
                    self.stats['simple_requests'] += 1
                    if self.logger:
                        self.logger.debug("[BG] Requête simple, pas de plan nécessaire")

                # Mettre à jour temps moyen de planification
                elapsed = time.time() - start_time
                if self.stats['total_requests'] > 0:
                    self.stats['avg_planning_time'] = (
                        (self.stats['avg_planning_time'] * (self.stats['total_requests'] - 1) + elapsed) /
                        self.stats['total_requests']
                    )

                # Callback planification complète
                if self.on_planning_complete:
                    try:
                        self.on_planning_complete(plan, analysis)
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Erreur callback on_planning_complete: {e}")

                # Marquer la tâche comme terminée
                self.request_queue.task_done()

            except Exception as e:
                self.stats['errors'] += 1
                if self.logger:
                    self.logger.error(f"[BG] Erreur dans planning_loop: {e}")

                # Callback erreur
                if self.on_error:
                    try:
                        self.on_error(e)
                    except:
                        pass

    def analyze_request_async(self, user_request: str, request_id: str = None) -> bool:
        """
        Ajoute une requête à la queue pour analyse en arrière-plan

        Args:
            user_request: Requête utilisateur à analyser
            request_id: ID optionnel pour tracer la requête

        Returns:
            True si ajouté à la queue, False si queue pleine
        """
        if not self.is_running:
            if self.logger:
                self.logger.warning("BackgroundPlanner non démarré, impossible d'ajouter requête")
            return False

        try:
            request_data = {
                'request': user_request,
                'id': request_id or f"req_{int(time.time() * 1000)}",
                'timestamp': datetime.now().isoformat()
            }

            self.request_queue.put_nowait(request_data)

            if self.logger:
                self.logger.debug(f"[BG] Requête ajoutée à la queue: {user_request[:50]}...")

            return True

        except queue.Full:
            if self.logger:
                self.logger.warning("[BG] Queue de requêtes pleine, requête ignorée")
            return False

    def get_latest_plan(self) -> Optional[Dict]:
        """
        Récupère le dernier plan généré sans bloquer

        Returns:
            Dernier plan généré ou None
        """
        return self.latest_plan

    def get_latest_analysis(self) -> Optional[Dict]:
        """
        Récupère la dernière analyse effectuée

        Returns:
            Dernière analyse ou None
        """
        return self.latest_analysis

    def get_plan_from_queue(self) -> Optional[Dict]:
        """
        Récupère un plan de la queue de résultats (non-bloquant)

        Returns:
            Dict avec 'plan', 'analysis', 'request_id' ou None
        """
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None

    def clear_queue(self):
        """Vide la queue de requêtes en attente"""
        while not self.request_queue.empty():
            try:
                self.request_queue.get_nowait()
                self.request_queue.task_done()
            except queue.Empty:
                break

        if self.logger:
            self.logger.info("[BG] Queue de requêtes vidée")

    def clear_results(self):
        """Vide la queue de résultats"""
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except queue.Empty:
                break

        self.latest_plan = None
        self.latest_analysis = None

        if self.logger:
            self.logger.info("[BG] Résultats effacés")

    def get_stats(self) -> Dict:
        """
        Récupère les statistiques du planificateur

        Returns:
            Dict avec statistiques
        """
        return {
            **self.stats,
            'is_running': self.is_running,
            'queue_size': self.request_queue.qsize(),
            'results_available': self.result_queue.qsize(),
            'has_latest_plan': self.latest_plan is not None
        }

    def is_busy(self) -> bool:
        """
        Vérifie si le planificateur traite actuellement une requête

        Returns:
            True si occupé, False sinon
        """
        return not self.request_queue.empty()

    def __enter__(self):
        """Context manager: démarrage"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: arrêt"""
        self.stop()
        return False
