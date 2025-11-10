"""
Display Manager - Gestion de l'affichage et des statistiques du terminal

Ce module contient toutes les méthodes d'affichage et de statistiques,
ainsi que les callbacks pour le mode agent.

Refactorisé pour utiliser Rich Console et composants Rich réutilisables.
"""

import requests
from typing import Optional, Dict, Any, List
from simple_term_menu import TerminalMenu

from src.terminal.rich_console import get_console
from src.terminal.rich_components import (
    create_result_panel,
    create_error_panel,
    create_warning_panel,
    create_models_table,
    create_history_table,
    create_hardware_table,
    create_cache_stats_table,
    create_stats_table,
    create_agent_plan_table,
    create_status_text
)
from src.utils import InputValidator, HardwareOptimizer
from config import prompts, project_templates, constants


class DisplayManager:
    """Gère l'affichage et les statistiques du terminal avec Rich"""

    def __init__(self, components: dict):
        """
        Initialise le gestionnaire d'affichage

        Args:
            components: Dictionnaire contenant tous les composants nécessaires
                - settings: Configuration
                - logger: Logger
                - shell_engine: Moteur du shell
                - security: Validateur de sécurité
                - history_manager: Gestionnaire d'historique
                - ollama: Client Ollama
                - executor: Exécuteur de commandes
                - cache_manager: Gestionnaire de cache (optionnel)
                - agent: Agent autonome (optionnel)
                - input_validator: InputValidator
        """
        self.components = components
        self.settings = components['settings']
        self.logger = components['logger']
        self.shell_engine = components['shell_engine']
        self.security = components['security']
        self.history_manager = components['history_manager']
        self.ollama = components['ollama']
        self.executor = components['executor']
        self.cache_manager = components.get('cache_manager')
        self.agent = components.get('agent')
        self.input_validator = components.get('input_validator')
        self.user_config = components.get('user_config')

        # Console Rich unifiée
        self.console = get_console()

    # ═══════════════════════════════════════════════════════════════
    # AFFICHAGE DE RÉSULTATS
    # ═══════════════════════════════════════════════════════════════

    def display_result(self, result: dict):
        """
        Affiche le résultat d'une commande avec Rich

        Args:
            result: Résultat de l'exécution
        """
        if result['success']:
            if result.get('output'):
                output = self.security.sanitize_output(result['output'])
                panel = create_result_panel(output, title="Sortie", success=True)
                self.console.print(panel)
        else:
            self.console.error("Échec de l'exécution de la commande")

            if result.get('error'):
                panel = create_error_panel(result['error'], title="Erreur")
                self.console.print(panel)

    # ═══════════════════════════════════════════════════════════════
    # HISTORIQUE DES COMMANDES
    # ═══════════════════════════════════════════════════════════════

    def show_history(self):
        """Affiche l'historique des commandes dans une table Rich"""
        history = self.history_manager.get_recent(20)

        if not history:
            self.console.warning("Aucune commande dans l'historique")
            return

        # Préparer les données avec les timestamps
        history_data = []
        for entry in history:
            timestamp = entry.get('timestamp', '')
            if timestamp:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = timestamp[:8]
            else:
                time_str = '??:??:??'

            history_data.append({
                'command': entry['command'],
                'success': entry.get('success', True),
                'timestamp': time_str
            })

        # Créer et afficher la table
        table = create_history_table(history_data, limit=20, show_timestamps=True)
        self.console.print(table)

        # Statistiques
        stats = self.history_manager.get_statistics()
        self.console.print(
            f"\n[label]Total:[/label] {len(self.history_manager)} commandes | "
            f"[label]Taux de succès:[/label] [success]{stats['success_rate']:.1f}%[/success]"
        )
        self.console.print("\n[dim]Utilisez '/history search <terme>' pour rechercher[/dim]")

    # ═══════════════════════════════════════════════════════════════
    # MODÈLES OLLAMA
    # ═══════════════════════════════════════════════════════════════

    def list_models(self):
        """Liste les modèles Ollama disponibles et permet de changer de modèle"""
        with self.console.create_status("Récupération des modèles disponibles..."):
            try:
                response = requests.get(f"{self.settings.ollama_host}/api/tags", timeout=5)
                response.raise_for_status()
                data = response.json()
                models_info = data.get('models', [])
            except Exception as e:
                self.console.error(f"Erreur lors de la récupération des modèles: {e}")
                return

        if not models_info:
            self.console.error("Aucun modèle trouvé")
            return

        # Préparer les données pour la table
        models_data = []
        for model_info in models_info:
            models_data.append({
                'name': model_info['name'],
                'size': self._format_model_size(model_info.get('size', 0))
            })

        # Afficher la table
        table = create_models_table(models_data, current_model=self.settings.ollama_model)
        self.console.print(table)

        # Si un seul modèle, pas besoin de menu
        if len(models_info) == 1:
            return

        # Proposer de changer de modèle
        self.console.print("\n[info]Voulez-vous changer de modèle?[/info]")
        response = input("   Tapez 'o' pour oui, ou Entrée pour continuer: ").strip().lower()

        if response not in ['o', 'oui', 'y', 'yes']:
            return

        # Créer le menu interactif
        self._show_model_selection_menu(models_info)

    def _show_model_selection_menu(self, models_info: List[Dict[str, Any]]):
        """Affiche le menu de sélection de modèle"""
        model_names = [m['name'] for m in models_info]
        menu_options = []

        for model_info in models_info:
            name = model_info['name']
            size = self._format_model_size(model_info.get('size', 0))
            marker = " [success]✓[/success]" if name == self.settings.ollama_model else ""
            menu_options.append(f"{name} ({size}){marker}")

        try:
            # Index du modèle actuel
            current_index = model_names.index(self.settings.ollama_model) if self.settings.ollama_model in model_names else 0

            terminal_menu = TerminalMenu(
                menu_options,
                title="Sélectionnez un modèle (↑↓ pour naviguer, Entrée pour valider, Ctrl+C pour annuler):",
                cursor_index=current_index
            )

            menu_index = terminal_menu.show()

            if menu_index is None:
                self.console.warning("Sélection annulée")
                return

            selected_model = model_names[menu_index]

            if selected_model == self.settings.ollama_model:
                self.console.info(f"Modèle inchangé: {selected_model}")
                return

            # Changer le modèle
            old_model = self.settings.ollama_model
            self.settings.ollama_model = selected_model
            self.ollama.model = selected_model

            # Sauvegarder le modèle dans la configuration utilisateur
            if self.user_config:
                self.user_config.save_last_model(selected_model)

            self.console.success(f"Modèle changé: {old_model} → {selected_model}")

            if self.logger:
                self.logger.info(f"Changement de modèle: {old_model} → {selected_model}")

        except Exception as e:
            self.console.error(f"Erreur lors de la sélection: {e}")

    def _format_model_size(self, size_bytes: int) -> str:
        """
        Formate la taille d'un modèle en unités lisibles

        Args:
            size_bytes: Taille en bytes

        Returns:
            Taille formatée (ex: "4.1 GB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    # ═══════════════════════════════════════════════════════════════
    # INFORMATIONS SYSTÈME
    # ═══════════════════════════════════════════════════════════════

    def show_system_info(self):
        """Affiche les informations système dans une table"""
        info = self.executor.get_system_info()

        # Préparer les données pour la table
        stats_data = {
            "Nom d'hôte": info.get('hostname', 'N/A'),
            "Utilisateur": info.get('username', 'N/A'),
            "Système": info.get('os', 'N/A'),
            "Uptime": info.get('uptime', 'N/A'),
            "Répertoire courant": info.get('current_dir', 'N/A')
        }

        table = create_stats_table(stats_data, title="Informations Système")
        self.console.print(table)

    def show_hardware_info(self):
        """Affiche les informations hardware et optimisations"""
        try:
            optimizer = HardwareOptimizer(self.logger)
            report = optimizer.get_optimization_report_dict()

            # Utiliser le composant hardware_table
            table = create_hardware_table(report)
            self.console.print(table)

        except Exception as e:
            self.console.error(f"Erreur lors de la récupération des infos hardware: {e}")
            self.logger.error(f"Erreur hardware info: {e}")

    # ═══════════════════════════════════════════════════════════════
    # TEMPLATES DE PROJETS
    # ═══════════════════════════════════════════════════════════════

    def list_templates(self):
        """Liste les templates de projets disponibles"""
        templates = project_templates.list_templates()

        # Créer une table pour les templates
        stats_data = {}
        for name, description in templates.items():
            stats_data[name] = description

        table = create_stats_table(stats_data, title="Templates de Projets Disponibles")
        self.console.print(table)

        self.console.print("\n[dim]Utilisez ces templates en demandant: 'crée un projet [type]'[/dim]")
        self.console.print("[dim]Ou utilisez /agent pour des projets personnalisés[/dim]")

    # ═══════════════════════════════════════════════════════════════
    # CACHE OLLAMA
    # ═══════════════════════════════════════════════════════════════

    def show_cache_stats(self):
        """Affiche les statistiques du cache Ollama"""
        if not self.cache_manager:
            panel = create_warning_panel(
                "Le cache n'est pas activé\n"
                "Activez-le dans .env avec CACHE_ENABLED=true"
            )
            self.console.print(panel)
            return

        try:
            stats = self.ollama.get_cache_stats()
            table = create_cache_stats_table(stats)
            self.console.print(table)

        except Exception as e:
            self.console.error(f"Erreur: {e}")
            self.logger.error(f"Erreur affichage stats cache: {e}")

    def clear_cache(self):
        """Efface le cache Ollama"""
        if not self.cache_manager:
            panel = create_warning_panel("Le cache n'est pas activé")
            self.console.print(panel)
            return

        if not self.input_validator.confirm_action(
            "Attention: Cette action va effacer tout le cache!\nÊtes-vous sûr?"
        ):
            self.console.error(constants.ERROR_MESSAGES['OPERATION_CANCELLED'])
            return

        try:
            self.ollama.clear_cache()
            self.console.success("Cache effacé avec succès!")
            self.logger.info("Cache Ollama effacé par l'utilisateur")

        except Exception as e:
            self.console.error(f"Erreur lors de l'effacement du cache: {e}")
            self.logger.error(f"Erreur effacement cache: {e}")

    # ═══════════════════════════════════════════════════════════════
    # SNAPSHOTS & ROLLBACK
    # ═══════════════════════════════════════════════════════════════

    def show_snapshots(self):
        """Affiche la liste des snapshots disponibles"""
        if not self.agent:
            self.console.error(constants.ERROR_MESSAGES['NO_AGENT'])
            return

        try:
            snapshots = self.agent.list_snapshots()

            if not snapshots:
                self.console.warning("Aucun snapshot disponible")
                return

            # Créer une table pour les snapshots
            stats_data = {}
            for idx, snapshot in enumerate(snapshots, 1):
                timestamp = snapshot.get('timestamp', 'N/A')
                project = snapshot.get('project', 'N/A')
                stats_data[f"#{idx} - {timestamp}"] = project

            table = create_stats_table(stats_data, title="Snapshots Disponibles")
            self.console.print(table)

        except Exception as e:
            self.console.error(f"Erreur: {e}")
            self.logger.error(f"Erreur affichage snapshots: {e}")

    def restore_snapshot(self, snapshot_id: Optional[str] = None):
        """Restaure un snapshot"""
        if not self.agent:
            self.console.error(constants.ERROR_MESSAGES['NO_AGENT'])
            return

        # Message de confirmation
        msg = f"Attention: Vous allez restaurer le snapshot: {snapshot_id if snapshot_id else 'dernier'}\n"
        msg += "Toutes les modifications actuelles seront perdues!"

        if not self.input_validator.confirm_action(msg):
            self.console.error("Rollback annulé")
            return

        with self.console.create_status("Restauration en cours..."):
            try:
                result = self.agent.rollback_last_execution(snapshot_id)

                if result['success']:
                    self.console.success("Rollback réussi!")
                    self.console.print(f"   Projet restauré: {result['project_path']}")
                    self.logger.info(f"Rollback effectué vers: {result.get('snapshot_id')}")
                else:
                    self.console.error(f"Erreur lors du rollback: {result.get('error')}")
                    self.logger.error(f"Erreur rollback: {result.get('error')}")

            except Exception as e:
                self.console.error(f"Erreur: {e}")
                self.logger.error(f"Erreur rollback: {e}")

    def show_rollback_stats(self):
        """Affiche les statistiques de rollback"""
        if not self.agent:
            self.console.error(constants.ERROR_MESSAGES['NO_AGENT'])
            return

        try:
            stats = self.agent.get_rollback_stats()
            table = create_stats_table(stats, title="Statistiques de Rollback")
            self.console.print(table)

        except Exception as e:
            self.console.error(f"Erreur: {e}")
            self.logger.error(f"Erreur stats rollback: {e}")

    # ═══════════════════════════════════════════════════════════════
    # SÉCURITÉ & CORRECTIONS
    # ═══════════════════════════════════════════════════════════════

    def show_security_report(self):
        """Affiche le rapport de sécurité"""
        try:
            report = self.security.get_security_report()
            table = create_stats_table(report, title="Rapport de Sécurité")
            self.console.print(table)

        except Exception as e:
            self.console.error(f"Erreur: {e}")
            self.logger.error(f"Erreur rapport sécurité: {e}")

    def show_correction_stats(self):
        """Affiche les statistiques d'auto-correction"""
        if not self.agent:
            self.console.error(constants.ERROR_MESSAGES['NO_AGENT'])
            return

        try:
            stats = self.agent.get_correction_stats()
            table = create_stats_table(stats, title="Statistiques d'Auto-correction")
            self.console.print(table)

        except Exception as e:
            self.console.error(f"Erreur: {e}")
            self.logger.error(f"Erreur stats corrections: {e}")

    def show_last_error(self):
        """Affiche l'analyse de la dernière erreur"""
        if not self.agent:
            self.console.error(constants.ERROR_MESSAGES['NO_AGENT'])
            return

        try:
            analysis = self.agent.get_last_error_analysis()

            if not analysis:
                self.console.warning("Aucune erreur récente analysée")
                return

            # Afficher l'analyse dans un panel
            content = f"Type: {analysis.get('error_type', 'N/A')}\n"
            content += f"Message: {analysis.get('error_message', 'N/A')}\n"

            if analysis.get('auto_fix'):
                content += f"\nCorrection tentée: {analysis['auto_fix']}"

            panel = create_error_panel(content, title="Analyse de la Dernière Erreur")
            self.console.print(panel)

        except Exception as e:
            self.console.error(f"Erreur: {e}")
            self.logger.error(f"Erreur affichage erreur: {e}")

    # ═══════════════════════════════════════════════════════════════
    # STATUT DU SHELL
    # ═══════════════════════════════════════════════════════════════

    def show_shell_status(self):
        """Affiche le statut du shell et les statistiques"""
        stats = self.shell_engine.get_statistics()

        # Informations principales
        self.console.print("\n[title]STATUT DU SHELL COTER[/title]")
        self.console.print()

        mode = stats['current_mode'].upper()
        mode_style = f"mode.{stats['current_mode']}"
        self.console.print(f"[{mode_style}]Mode actuel:[/{mode_style}] {mode}")
        self.console.print(f"[dim]{self.shell_engine.get_mode_description()}[/dim]")
        self.console.print()

        # Statistiques de session
        session_data = {
            "Mode de démarrage": stats['session_start_mode'],
            "Changements de mode": stats['mode_changes'],
            "Total de commandes": stats['total_commands']
        }

        table = create_stats_table(session_data, title="Statistiques de Session")
        self.console.print(table)

        # Commandes par mode
        if stats['command_counts']:
            self.console.print("\n[subtitle]Commandes par mode:[/subtitle]")
            for mode, count in stats['command_counts'].items():
                self.console.print(f"   [label]{mode.upper()}:[/label] {count}")

        # Historique des modes
        if len(stats['mode_history']) > 1:
            history_display = " → ".join(stats['mode_history'])
            self.console.print(f"\n[subtitle]Historique des modes:[/subtitle]")
            self.console.print(f"   [dim]{history_display}[/dim]")

        self.console.print()

    # ═══════════════════════════════════════════════════════════════
    # CALLBACKS POUR LE MODE AGENT
    # ═══════════════════════════════════════════════════════════════

    def on_agent_step_start(self, step_number: int, step: dict):
        """Callback appelé au début de chaque étape de l'agent"""
        total_steps = len(self.agent.current_plan.get('steps', []))
        description = step.get('description', 'Action')

        # Icônes pour les actions
        action_icons = {
            'create_structure': '[dim]📁[/dim]',
            'create_file': '[dim]📝[/dim]',
            'run_command': '[dim]⚙[/dim]',
            'git_commit': '[dim]📦[/dim]'
        }
        icon = action_icons.get(step.get('action', ''), '[dim]🔨[/dim]')

        self.console.print(f"\n[label][{step_number}/{total_steps}][/label] {icon}  {description}...")

    def on_agent_step_complete(self, step_number: int, step: dict, result: dict):
        """Callback appelé à la fin de chaque étape de l'agent"""
        if result.get('success'):
            # Afficher des détails selon le type d'action
            action = step.get('action')

            if action == 'create_file':
                lines = result.get('lines_written', 0)
                file_path = result.get('file_path', 'N/A')
                status = create_status_text(True, f"Fichier créé: {file_path} ({lines} lignes)")
                self.console.print("      ", status)

            elif action == 'create_structure':
                count = result.get('count', 0)
                plural = 's' if count > 1 else ''
                status = create_status_text(True, f"{count} dossier{plural} créé{plural}")
                self.console.print("      ", status)

            elif action == 'git_commit':
                message = result.get('message', 'OK')
                status = create_status_text(True, f"Commit: {message}")
                self.console.print("      ", status)

            elif action == 'run_command':
                attempts = result.get('attempts', 1)

                if attempts > 1:
                    status = create_status_text(True, f"Terminé (après {attempts} tentatives)")
                    self.console.print("      ", status)

                    # Afficher l'historique de retry
                    retry_history = result.get('retry_history', [])
                    if retry_history:
                        self.console.print("         [dim]Retries:[/dim]")
                        for retry in retry_history:
                            attempt = retry['attempt']
                            error_type = retry['error_type']
                            confidence = int(retry.get('confidence', 0) * 100)
                            self.console.print(
                                f"            [dim]• Tentative {attempt}: {error_type} (confiance: {confidence}%)[/dim]"
                            )
                else:
                    status = create_status_text(True, "Terminé")
                    self.console.print("      ", status)
            else:
                status = create_status_text(True, "Terminé")
                self.console.print("      ", status)
        else:
            # Affichage en cas d'échec
            attempts = result.get('attempts', 0)

            if attempts > 1:
                status = create_status_text(False, f"Échec après {attempts} tentatives")
                self.console.print("      ", status)

                last_analysis = result.get('last_analysis')
                if last_analysis:
                    error_type = last_analysis.get('error_type', 'unknown')
                    self.console.print(f"         [dim]Type: {error_type}[/dim]")

                    if last_analysis.get('auto_fix'):
                        self.console.print(f"         [dim]Correction tentée: {last_analysis['auto_fix']}[/dim]")
            else:
                error_msg = result.get('error', 'Erreur inconnue')
                status = create_status_text(False, error_msg)
                self.console.print("      ", status)

    def on_agent_error(self, step_number: int, step: dict, error: dict):
        """Callback appelé en cas d'erreur dans l'agent"""
        error_msg = error.get('error', 'Erreur inconnue')
        self.console.error(f"Erreur à l'étape {step_number}")
        self.console.print(f"    [dim]{error_msg}[/dim]")

    # ═══════════════════════════════════════════════════════════════
    # PLANIFICATION EN ARRIÈRE-PLAN
    # ═══════════════════════════════════════════════════════════════

    def show_planning_indicator(self):
        """
        Affiche un indicateur discret de planification en cours
        Format minimal: ⚙️ Planning...
        """
        self.console.print("[dim]⚙️ Planning...[/dim]", end="")

    def hide_planning_indicator(self):
        """
        Efface l'indicateur de planification
        Utilise un retour chariot pour effacer la ligne
        """
        # Effacer la ligne avec des espaces puis retour à la ligne
        self.console.print("\r" + " " * 20 + "\r", end="")

    def show_plan_ready_notification(self, plan: dict, analysis: dict):
        """
        Affiche une notification discrète quand un plan est prêt

        Args:
            plan: Plan généré
            analysis: Analyse de la requête
        """
        from rich.panel import Panel

        project_type = analysis.get('project_type', 'unknown')
        step_count = len(plan.get('steps', []))

        notification = Panel(
            f"[dim]Plan prêt:[/dim] [info]{project_type}[/info]\n"
            f"[dim]{step_count} étapes préparées[/dim]\n\n"
            f"[dim]Tapez[/dim] [info]/plan[/info] [dim]pour consulter[/dim]",
            title="[bold cyan]⚙️ Plan Ready[/bold cyan]",
            border_style="cyan dim",
            padding=(0, 2),
            box=box.ROUNDED
        )

        self.console.print()
        self.console.print(notification)

    def show_background_plan(self, plan_data: dict):
        """
        Affiche un plan généré en arrière-plan avec formatage similaire au mode agent

        Args:
            plan_data: Dict contenant 'plan', 'analysis', 'request_id'
        """
        plan = plan_data.get('plan', {})
        analysis = plan_data.get('analysis', {})
        request_id = plan_data.get('request_id', 'unknown')

        # Afficher l'en-tête
        project_type = analysis.get('project_type', 'unknown')
        user_request = plan.get('_metadata', {}).get('user_request', '')
        planning_time = plan.get('_metadata', {}).get('planning_time', 0)

        self.console.print()
        self.console.print("[title]PLAN GÉNÉRÉ EN ARRIÈRE-PLAN[/title]")
        self.console.print()
        self.console.print(f"[label]Type:[/label] {project_type}")
        self.console.print(f"[label]Requête:[/label] {user_request}")
        self.console.print(f"[label]Temps de génération:[/label] {planning_time:.2f}s")
        self.console.print()

        # Utiliser la table existante pour afficher le plan
        if hasattr(self.agent, 'planner'):
            # Utiliser la méthode display_plan du ProjectPlanner
            plan_display = self.agent.planner.display_plan(plan)
            self.console.print(plan_display)
        else:
            # Fallback: affichage simple
            steps = plan.get('steps', [])
            table = create_agent_plan_table(steps)
            self.console.print(table)

        self.console.print()
        self.console.print("[dim]ID du plan:[/dim] [dim]{}[/dim]".format(request_id))

    def show_plan_stats(self, stats: dict):
        """
        Affiche les statistiques du système de planification en arrière-plan

        Args:
            stats: Dict avec les statistiques
        """
        stats_data = {
            "Total de requêtes": stats.get('total_requests', 0),
            "Plans générés": stats.get('plans_generated', 0),
            "Requêtes simples": stats.get('simple_requests', 0),
            "Erreurs": stats.get('errors', 0),
            "Temps moyen de planification": f"{stats.get('avg_planning_time', 0):.2f}s",
            "Planificateur actif": "Oui" if stats.get('is_running', False) else "Non",
            "Requêtes en queue": stats.get('queue_size', 0),
            "Plans disponibles": stats.get('results_available', 0)
        }

        table = create_stats_table(stats_data, title="Statistiques de Planification en Arrière-plan")
        self.console.print(table)
