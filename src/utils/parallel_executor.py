"""Exécuteur parallèle pour les tâches indépendantes de l'agent autonome"""

import concurrent.futures
from typing import List, Dict, Callable, Any, Optional
import time
import multiprocessing
import platform
from config import constants

class ParallelExecutor:
    """Exécute des tâches en VRAI parallèle pour accélérer l'agent autonome (multiprocessing)"""

    def __init__(self, max_workers: int = None, logger=None, executor_type: str = None,
                 persistent_pool: bool = True):
        """
        Initialise l'exécuteur parallèle

        Args:
            max_workers: Nombre maximum de workers (None = auto-détection)
            logger: Logger pour les messages
            executor_type: 'process' ou 'thread' (None = utiliser constante)
            persistent_pool: Si True, maintient un pool persistant (CSAPP Ch.8 - réduit overhead ARM)
        """
        self.max_workers = max_workers or self._get_optimal_workers()
        self.logger = logger
        self.persistent_pool = persistent_pool

        # Détection ARM pour optimisations spécifiques
        self.is_arm = self._detect_arm()

        # Utiliser la constante si non spécifié
        self.executor_type = executor_type or constants.PARALLEL_EXECUTOR_TYPE

        # Pool persistant pour réduire overhead de création/destruction (CSAPP Ch.8)
        self._pool: Optional[concurrent.futures.Executor] = None
        self._pool_task_count = 0
        self._pool_max_tasks = 100 if self.is_arm else 200  # Recycler plus souvent sur ARM

        # Configurer multiprocessing pour Windows
        if self.executor_type == 'process':
            try:
                # Vérifier si la méthode n'est pas déjà configurée
                current_method = multiprocessing.get_start_method(allow_none=True)
                if current_method is None:
                    multiprocessing.set_start_method(constants.PARALLEL_PROCESS_START_METHOD, force=False)
                    if self.logger:
                        self.logger.debug(f"Méthode multiprocessing configurée: {constants.PARALLEL_PROCESS_START_METHOD}")
                elif current_method != constants.PARALLEL_PROCESS_START_METHOD:
                    if self.logger:
                        self.logger.warning(f"Méthode multiprocessing déjà configurée ({current_method}), forçage en {constants.PARALLEL_PROCESS_START_METHOD}")
                    multiprocessing.set_start_method(constants.PARALLEL_PROCESS_START_METHOD, force=True)
                else:
                    if self.logger:
                        self.logger.debug(f"Méthode multiprocessing déjà correctement configurée: {current_method}")
            except RuntimeError as e:
                # Déjà configuré avec la même méthode
                if self.logger:
                    self.logger.debug("Méthode multiprocessing déjà configurée (RuntimeError ignoré)")
            except Exception as e:
                # Autre erreur lors de la configuration
                if self.logger:
                    self.logger.error(f"Erreur configuration multiprocessing: {e}")
                raise

        if self.logger:
            mode = "MULTIPROCESSING (vrai parallélisme)" if self.executor_type == 'process' else "THREADING (concurrent I/O)"
            pool_mode = "pool persistant" if self.persistent_pool else "pool temporaire"
            arm_info = " [ARM optimisé]" if self.is_arm else ""
            self.logger.info(f"ParallelExecutor initialisé avec {self.max_workers} workers en mode {mode} ({pool_mode}){arm_info}")

    def _detect_arm(self) -> bool:
        """
        Détecte si on est sur architecture ARM (CSAPP Ch.8)

        Returns:
            True si ARM
        """
        machine = platform.machine().lower()
        arm_archs = ['aarch64', 'armv7l', 'armv8', 'arm64']
        return any(arch in machine for arch in arm_archs)

    def _get_optimal_workers(self) -> int:
        """
        Détermine le nombre optimal de workers selon le hardware

        Returns:
            Nombre de workers recommandé
        """
        import os
        import psutil

        # CPU count
        cpu_count = os.cpu_count() or 2

        # RAM disponible
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)

        # Sur Raspberry Pi (RAM limitée), limiter les workers
        if ram_gb < 4:
            # Raspberry Pi avec peu de RAM
            return min(2, cpu_count)
        elif ram_gb < 8:
            # 4-8 GB RAM
            return min(4, cpu_count)
        else:
            # 8+ GB RAM
            return min(cpu_count, 8)

    def _get_pool(self) -> concurrent.futures.Executor:
        """
        Obtient ou crée le pool d'exécution (CSAPP Ch.8 - pool persistant)

        Returns:
            Pool d'exécution
        """
        # Si pool existe et pas besoin de recycler, le réutiliser
        if self._pool is not None and self._pool_task_count < self._pool_max_tasks:
            return self._pool

        # Sinon, recycler le pool
        if self._pool is not None:
            if self.logger:
                self.logger.debug(f"Recyclage du pool après {self._pool_task_count} tâches")
            self._recycle_pool()

        # Créer nouveau pool
        executor_class = (concurrent.futures.ProcessPoolExecutor
                         if self.executor_type == 'process'
                         else concurrent.futures.ThreadPoolExecutor)

        self._pool = executor_class(max_workers=self.max_workers)
        self._pool_task_count = 0

        if self.logger:
            pool_type = "Process" if self.executor_type == 'process' else "Thread"
            self.logger.debug(f"{pool_type}Pool créé avec {self.max_workers} workers")

        return self._pool

    def _recycle_pool(self):
        """Recycle le pool d'exécution pour libérer ressources (CSAPP Ch.8)"""
        if self._pool is not None:
            try:
                self._pool.shutdown(wait=True)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Erreur lors du recyclage du pool: {e}")
            finally:
                self._pool = None
                self._pool_task_count = 0

    def shutdown(self):
        """Arrête proprement le pool d'exécution"""
        if self._pool is not None:
            if self.logger:
                self.logger.debug("Arrêt du pool d'exécution")
            self._recycle_pool()

    def __enter__(self):
        """Support du context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Nettoyage automatique à la sortie du context manager"""
        self.shutdown()
        return False

    def __del__(self):
        """Nettoyage lors de la destruction de l'objet"""
        self.shutdown()

    def _execute_tasks(self, executor: concurrent.futures.Executor,
                      tasks: List[Dict], executor_func: Callable,
                      results: List) -> List[Dict]:
        """
        Exécute les tâches sur un executor donné

        Args:
            executor: Pool d'exécution
            tasks: Liste de tâches
            executor_func: Fonction à appeler
            results: Liste des résultats à remplir

        Returns:
            Liste des résultats
        """
        # Soumettre toutes les tâches
        future_to_index = {
            executor.submit(executor_func, task): i
            for i, task in enumerate(tasks)
        }

        # Récupérer les résultats au fur et à mesure
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                results[index] = result

                if self.logger:
                    self.logger.debug(f"Tâche {index + 1}/{len(tasks)} terminée")

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Erreur tâche {index}: {e}", exc_info=True)
                results[index] = {
                    'success': False,
                    'error': str(e),
                    'task_index': index
                }

        return results

    def execute_parallel(self, tasks: List[Dict], executor_func: Callable) -> List[Dict]:
        """
        Exécute une liste de tâches en VRAI parallèle (multiprocessing)

        Args:
            tasks: Liste de tâches (dicts avec les paramètres)
            executor_func: Fonction à appeler pour chaque tâche

        Returns:
            Liste des résultats dans le même ordre que les tâches
        """
        if not tasks:
            return []

        # Seuil minimum de tâches
        if len(tasks) < constants.MIN_TASKS_FOR_PARALLEL:
            # Pas assez de tâches, exécution séquentielle
            return [executor_func(task) for task in tasks]

        results = [None] * len(tasks)
        start_time = time.time()

        if self.logger:
            mode = "MULTIPROCESSING" if self.executor_type == 'process' else "THREADING"
            pool_info = f" [pool persistant, {self._pool_task_count} tâches]" if self.persistent_pool else ""
            self.logger.info(f"Exécution {mode} de {len(tasks)} tâches avec {self.max_workers} workers{pool_info}")

        try:
            # Utiliser pool persistant ou créer nouveau pool
            if self.persistent_pool:
                executor = self._get_pool()
                use_context_manager = False
            else:
                # Mode legacy: créer nouveau pool à chaque fois
                executor_class = (concurrent.futures.ProcessPoolExecutor
                                 if self.executor_type == 'process'
                                 else concurrent.futures.ThreadPoolExecutor)
                executor = executor_class(max_workers=self.max_workers)
                use_context_manager = True

            # Exécuter les tâches
            if use_context_manager:
                with executor:
                    results = self._execute_tasks(executor, tasks, executor_func, results)
            else:
                results = self._execute_tasks(executor, tasks, executor_func, results)
                # Incrémenter compteur pour recyclage
                self._pool_task_count += len(tasks)

        except Exception as e:
            # Fallback sur threading si multiprocessing échoue
            if self.executor_type == 'process' and constants.PARALLEL_FALLBACK_TO_THREAD:
                if self.logger:
                    self.logger.warning(f"Multiprocessing échoué ({e}), fallback sur threading")

                # Retry avec threading
                self.executor_type = 'thread'
                return self.execute_parallel(tasks, executor_func)
            else:
                raise

        elapsed = time.time() - start_time

        if self.logger:
            mode = "MULTIPROCESSING" if self.executor_type == 'process' else "THREADING"
            self.logger.info(f"Exécution {mode} terminée en {elapsed:.2f}s")

        return results

    def can_parallelize(self, steps: List[Dict]) -> List[List[int]]:
        """
        Analyse une liste d'étapes et détermine lesquelles peuvent être exécutées en parallèle

        Args:
            steps: Liste des étapes du plan

        Returns:
            Liste de groupes d'indices d'étapes parallélisables
            Exemple: [[0, 1, 2], [3], [4, 5]] signifie que 0,1,2 peuvent être en parallèle,
                     puis 3 seul, puis 4,5 en parallèle
        """
        groups = []
        current_group = []
        seen_files = set()
        seen_dirs = set()

        for i, step in enumerate(steps):
            action = step.get('action')
            can_add_to_group = True

            if action == 'create_file':
                file_path = step.get('file_path', '')

                # Vérifier si un fichier parent/enfant est déjà dans le groupe
                for seen_file in seen_files:
                    if file_path.startswith(seen_file) or seen_file.startswith(file_path):
                        can_add_to_group = False
                        break

                if can_add_to_group:
                    seen_files.add(file_path)
                    current_group.append(i)
                else:
                    # Finaliser le groupe actuel
                    if current_group:
                        groups.append(current_group)
                    current_group = [i]
                    seen_files = {file_path}
                    seen_dirs = set()

            elif action == 'create_structure':
                # Les créations de structure doivent être isolées
                if current_group:
                    groups.append(current_group)
                groups.append([i])
                current_group = []
                seen_files = set()
                seen_dirs = set()

            elif action == 'git_commit':
                # Git commit doit attendre toutes les étapes précédentes
                if current_group:
                    groups.append(current_group)
                groups.append([i])
                current_group = []
                seen_files = set()
                seen_dirs = set()

            elif action == 'run_command':
                # Les commandes shell ne peuvent pas être parallélisées (sauf cas spéciaux)
                if current_group:
                    groups.append(current_group)
                groups.append([i])
                current_group = []
                seen_files = set()
                seen_dirs = set()

            else:
                # Action inconnue, isoler par sécurité
                if current_group:
                    groups.append(current_group)
                groups.append([i])
                current_group = []
                seen_files = set()
                seen_dirs = set()

        # Ajouter le dernier groupe
        if current_group:
            groups.append(current_group)

        return groups

    def execute_step_group(self, steps: List[Dict], executor_func: Callable, callback: Callable = None) -> List[Dict]:
        """
        Exécute un groupe d'étapes en parallèle

        Args:
            steps: Liste d'étapes à exécuter
            executor_func: Fonction qui exécute une étape
            callback: Fonction callback optionnelle appelée après chaque étape

        Returns:
            Liste des résultats
        """
        if len(steps) == 1:
            # Une seule étape, exécution directe
            result = executor_func(steps[0])
            if callback:
                callback(steps[0], result)
            return [result]

        # Plusieurs étapes, paralléliser
        results = self.execute_parallel(steps, executor_func)

        # Appeler le callback pour chaque résultat
        if callback:
            for step, result in zip(steps, results):
                callback(step, result)

        return results

    def get_parallelization_stats(self, steps: List[Dict]) -> Dict[str, Any]:
        """
        Analyse les étapes et retourne des statistiques sur la parallélisation possible

        Args:
            steps: Liste des étapes

        Returns:
            Dict avec les statistiques
        """
        groups = self.can_parallelize(steps)

        total_steps = len(steps)
        parallel_groups = len(groups)
        steps_in_parallel = sum(len(g) for g in groups if len(g) > 1)
        sequential_steps = sum(len(g) for g in groups if len(g) == 1)

        max_parallel = max((len(g) for g in groups), default=1)

        # Estimation du gain de temps (approximatif)
        # Temps séquentiel = N étapes * temps moyen par étape
        # Temps parallèle = nombre de groupes * temps moyen par étape
        sequential_time_units = total_steps
        parallel_time_units = parallel_groups
        time_saving_percent = ((sequential_time_units - parallel_time_units) / sequential_time_units * 100) if sequential_time_units > 0 else 0

        return {
            'total_steps': total_steps,
            'parallel_groups': parallel_groups,
            'steps_parallelizable': steps_in_parallel,
            'steps_sequential': sequential_steps,
            'max_parallel_batch': max_parallel,
            'estimated_time_saving_percent': round(time_saving_percent, 1),
            'workers_available': self.max_workers
        }
