"""
Display Manager - Gestion de l'affichage et des statistiques du terminal

Ce module contient toutes les méthodes d'affichage et de statistiques,
ainsi que les callbacks pour le mode agent.
"""

import requests
from typing import Optional
from simple_term_menu import TerminalMenu
from src.utils import UIFormatter, StatsDisplayer, InputValidator, HardwareOptimizer
from config import prompts, project_templates, constants


class DisplayManager:
    """Gère l'affichage et les statistiques du terminal"""

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
                - ui: UIFormatter
                - stats_displayer: StatsDisplayer
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
        self.ui = components['ui']
        self.stats_displayer = components['stats_displayer']
        self.input_validator = components['input_validator']

    def display_result(self, result: dict):
        """
        Affiche le résultat d'une commande

        Args:
            result: Résultat de l'exécution
        """
        if result['success']:
            print(f"\n✅ Commande exécutée avec succès")
            if result.get('output'):
                print(f"\n📤 Sortie:")
                print("─" * 60)
                output = self.security.sanitize_output(result['output'])
                print(output)
                print("─" * 60)
        else:
            print(f"\n❌ Erreur lors de l'exécution")
            if result.get('error'):
                print(f"\n⚠️  Message d'erreur:")
                print("─" * 60)
                print(result['error'])
                print("─" * 60)

    def show_history(self):
        """Affiche l'historique des commandes"""
        history = self.history_manager.get_recent(20)  # Dernières 20 commandes

        if not history:
            print("\n📝 Aucune commande dans l'historique")
            return

        print("\n📝 Historique des commandes:")
        print("═" * 80)

        for i, entry in enumerate(history, 1):
            # Icônes selon le mode
            mode_icons = {
                'manual': '⌨️',
                'auto': '🤖',
                'agent': '🏗️'
            }
            icon = mode_icons.get(entry.get('mode', 'manual'), '❓')

            # Indicateur de succès
            status = '✅' if entry.get('success', True) else '❌'

            # Timestamp (simplifié)
            timestamp = entry.get('timestamp', '')
            if timestamp:
                # Garder seulement HH:MM:SS
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = timestamp[:8]
            else:
                time_str = '??:??:??'

            print(f"\n{i:2}. {icon} [{time_str}] {status} {entry['command']}")

        print("\n═" * 80)
        print(f"Total: {len(self.history_manager)} commandes | Affichées: {len(history)}")

        # Afficher les statistiques
        stats = self.history_manager.get_statistics()
        print(f"Taux de succès: {stats['success_rate']:.1f}%")
        print("\nUtilisez '/history search <terme>' pour rechercher")

    def list_models(self):
        """Liste les modèles Ollama disponibles et permet de changer de modèle"""
        print("\n🔍 Récupération des modèles disponibles...")

        # Récupérer les informations détaillées des modèles
        try:
            response = requests.get(f"{self.settings.ollama_host}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            models_info = data.get('models', [])
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des modèles: {e}")
            return

        if not models_info:
            print("❌ Aucun modèle trouvé")
            return

        # Afficher les modèles avec leurs informations
        print("\n📦 Modèles Ollama disponibles:")
        print("─" * 60)
        for model_info in models_info:
            name = model_info['name']
            size_bytes = model_info.get('size', 0)

            # Formater la taille
            size = self._format_model_size(size_bytes)

            # Marquer le modèle actuel
            marker = " ✓" if name == self.settings.ollama_model else ""
            print(f"  • {name:<30} ({size}){marker}")
        print("─" * 60)

        # Si un seul modèle, pas besoin de menu
        if len(models_info) == 1:
            return

        # Proposer de changer de modèle
        print("\n💡 Voulez-vous changer de modèle?")
        response = input("   Tapez 'o' pour oui, ou Entrée pour continuer: ").strip().lower()

        if response not in ['o', 'oui', 'y', 'yes']:
            return

        # Créer le menu interactif
        model_names = [m['name'] for m in models_info]
        menu_options = []

        for model_info in models_info:
            name = model_info['name']
            size = self._format_model_size(model_info.get('size', 0))
            marker = " ✓" if name == self.settings.ollama_model else ""
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
                print("\n⚠️  Sélection annulée")
                return

            selected_model = model_names[menu_index]

            if selected_model == self.settings.ollama_model:
                print(f"\n✓ Modèle inchangé: {selected_model}")
                return

            # Changer le modèle
            old_model = self.settings.ollama_model
            self.settings.ollama_model = selected_model
            self.ollama.model = selected_model

            print(f"\n✓ Modèle changé: {old_model} → {selected_model}")

            if self.logger:
                self.logger.info(f"Changement de modèle: {old_model} → {selected_model}")

        except Exception as e:
            print(f"\n❌ Erreur lors de la sélection: {e}")

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

    def show_system_info(self):
        """Affiche les informations système"""
        print("\n💻 Informations système:")
        print("═" * 70)

        info = self.executor.get_system_info()

        labels = {
            'hostname': 'Nom d\'hôte',
            'username': 'Utilisateur',
            'os': 'Système',
            'uptime': 'Uptime',
            'current_dir': 'Répertoire courant'
        }

        for key, value in info.items():
            label = labels.get(key, key)
            print(f"{label:20}: {value}")

        print("═" * 70)

    def list_templates(self):
        """Liste les templates de projets disponibles"""
        templates = project_templates.list_templates()

        print("\n📚 Templates de projets disponibles:")
        print("═" * 70)

        for name, description in templates.items():
            print(f"\n  • {name}")
            print(f"    {description}")

        print("\n═" * 70)
        print("\nUtilisez ces templates en demandant: 'crée un projet [type]'")
        print("Ou utilisez /agent pour des projets personnalisés")

    def show_cache_stats(self):
        """Affiche les statistiques du cache Ollama"""
        if not self.cache_manager:
            self.ui.print_warning("Le cache n'est pas activé")
            print("   Activez-le dans .env avec CACHE_ENABLED=true")
            return

        try:
            stats = self.ollama.get_cache_stats()
            self.stats_displayer.display_cache_stats(stats)
        except Exception as e:
            self.ui.print_error(f"Erreur: {e}")
            self.logger.error(f"Erreur affichage stats cache: {e}")

    def clear_cache(self):
        """Efface le cache Ollama"""
        if not self.cache_manager:
            self.ui.print_warning("Le cache n'est pas activé")
            return

        if not self.input_validator.confirm_action(
            "⚠️  Attention: Cette action va effacer tout le cache!\nÊtes-vous sûr?"
        ):
            self.ui.print_error(constants.ERROR_MESSAGES['OPERATION_CANCELLED'])
            return

        try:
            self.ollama.clear_cache()
            self.ui.print_success("Cache effacé avec succès!")
            self.logger.info("Cache Ollama effacé par l'utilisateur")
        except Exception as e:
            self.ui.print_error(f"Erreur lors de l'effacement du cache: {e}")
            self.logger.error(f"Erreur effacement cache: {e}")

    def show_hardware_info(self):
        """Affiche les informations hardware et optimisations"""
        print("\n" + "="*60)
        print("🖥️  INFORMATIONS HARDWARE")
        print("="*60)

        try:
            optimizer = HardwareOptimizer(self.logger)
            print(optimizer.get_optimization_report())
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des infos hardware: {e}")
            self.logger.error(f"Erreur hardware info: {e}")

    def show_snapshots(self):
        """Affiche la liste des snapshots disponibles"""
        if not self.agent:
            self.ui.print_error(constants.ERROR_MESSAGES['NO_AGENT'])
            return

        try:
            snapshots = self.agent.list_snapshots()
            self.stats_displayer.display_snapshots_list(snapshots)
        except Exception as e:
            self.ui.print_error(f"Erreur: {e}")
            self.logger.error(f"Erreur affichage snapshots: {e}")

    def restore_snapshot(self, snapshot_id: Optional[str] = None):
        """Restaure un snapshot"""
        if not self.agent:
            self.ui.print_error(constants.ERROR_MESSAGES['NO_AGENT'])
            return

        # Message de confirmation
        msg = f"Attention: Vous allez restaurer le snapshot: {snapshot_id if snapshot_id else 'dernier'}\n"
        msg += "Toutes les modifications actuelles seront perdues!"

        if not self.input_validator.confirm_action(msg):
            self.ui.print_error("Rollback annulé")
            return

        print("\n🔄 Restauration en cours...")

        try:
            result = self.agent.rollback_last_execution(snapshot_id)

            if result['success']:
                self.ui.print_success("Rollback réussi!")
                print(f"   Projet restauré: {result['project_path']}")
                self.logger.info(f"Rollback effectué vers: {result.get('snapshot_id')}")
            else:
                self.ui.print_error(f"Erreur lors du rollback: {result.get('error')}")
                self.logger.error(f"Erreur rollback: {result.get('error')}")

        except Exception as e:
            self.ui.print_error(f"Erreur: {e}")
            self.logger.error(f"Erreur rollback: {e}")

    def show_rollback_stats(self):
        """Affiche les statistiques de rollback"""
        if not self.agent:
            self.ui.print_error(constants.ERROR_MESSAGES['NO_AGENT'])
            return

        try:
            stats = self.agent.get_rollback_stats()
            self.stats_displayer.display_rollback_stats(stats)
        except Exception as e:
            self.ui.print_error(f"Erreur: {e}")
            self.logger.error(f"Erreur stats rollback: {e}")

    def show_security_report(self):
        """Affiche le rapport de sécurité"""
        try:
            report = self.security.get_security_report()
            self.stats_displayer.display_security_report(report)
        except Exception as e:
            self.ui.print_error(f"Erreur: {e}")
            self.logger.error(f"Erreur rapport sécurité: {e}")

    def show_correction_stats(self):
        """Affiche les statistiques d'auto-correction"""
        if not self.agent:
            self.ui.print_error(constants.ERROR_MESSAGES['NO_AGENT'])
            return

        try:
            stats = self.agent.get_correction_stats()
            self.stats_displayer.display_correction_stats(stats)
        except Exception as e:
            self.ui.print_error(f"Erreur: {e}")
            self.logger.error(f"Erreur stats corrections: {e}")

    def show_last_error(self):
        """Affiche l'analyse de la dernière erreur"""
        if not self.agent:
            self.ui.print_error(constants.ERROR_MESSAGES['NO_AGENT'])
            return

        try:
            analysis = self.agent.get_last_error_analysis()
            self.stats_displayer.display_error_analysis(analysis)
        except Exception as e:
            self.ui.print_error(f"Erreur: {e}")
            self.logger.error(f"Erreur affichage erreur: {e}")

    def show_shell_status(self):
        """Affiche le statut du shell et les statistiques"""
        stats = self.shell_engine.get_statistics()

        print("\n" + "="*60)
        print("🖥️  STATUT DU SHELL COTER")
        print("="*60)

        mode_icon = self.shell_engine.get_prompt_symbol()
        print(f"\n{mode_icon}  Mode actuel: {stats['current_mode'].upper()}")
        print(f"   {self.shell_engine.get_mode_description()}")

        print(f"\n📊 Statistiques de session:")
        print(f"   • Mode de démarrage: {stats['session_start_mode']}")
        print(f"   • Changements de mode: {stats['mode_changes']}")
        print(f"   • Total de commandes: {stats['total_commands']}")

        print(f"\n📈 Commandes par mode:")
        for mode, count in stats['command_counts'].items():
            print(f"   • {mode.upper()}: {count}")

        if len(stats['mode_history']) > 1:
            print(f"\n🔄 Historique des modes:")
            history_display = " → ".join(stats['mode_history'])
            print(f"   {history_display}")

        print("="*60)

    # ========== Callbacks pour le mode Agent ==========

    def on_agent_step_start(self, step_number: int, step: dict):
        """Callback appelé au début de chaque étape de l'agent"""
        total_steps = len(self.agent.current_plan.get('steps', []))
        description = step.get('description', 'Action')
        action_icon = {
            'create_structure': '📁',
            'create_file': '📝',
            'run_command': '⚙️',
            'git_commit': '📦'
        }.get(step.get('action', ''), '🔨')

        print(f"\n[{step_number}/{total_steps}] {action_icon}  {description}...")

    def on_agent_step_complete(self, step_number: int, step: dict, result: dict):
        """Callback appelé à la fin de chaque étape de l'agent"""
        if result.get('success'):
            # Afficher des détails selon le type d'action
            if step.get('action') == 'create_file':
                lines = result.get('lines_written', 0)
                print(f"      ✅ Fichier créé: {result.get('file_path')} ({lines} lignes)")
            elif step.get('action') == 'create_structure':
                count = result.get('count', 0)
                print(f"      ✅ {count} dossier{'s' if count > 1 else ''} créé{'s' if count > 1 else ''}")
            elif step.get('action') == 'git_commit':
                print(f"      ✅ Commit: {result.get('message', 'OK')}")
            elif step.get('action') == 'run_command':
                # Phase 3: Afficher les infos de retry si présentes
                attempts = result.get('attempts', 1)
                if attempts > 1:
                    print(f"      ✅ Terminé (après {attempts} tentatives)")
                    # Afficher l'historique de retry
                    retry_history = result.get('retry_history', [])
                    if retry_history:
                        print(f"         🔄 Retries:")
                        for retry in retry_history:
                            print(f"            • Tentative {retry['attempt']}: {retry['error_type']} (confiance: {int(retry.get('confidence', 0)*100)}%)")
                else:
                    print(f"      ✅ Terminé")
            else:
                print(f"      ✅ Terminé")
        else:
            # Phase 3: Afficher les infos d'analyse d'erreur
            attempts = result.get('attempts', 0)
            if attempts > 1:
                print(f"      ⚠️  Échec après {attempts} tentatives")
                last_analysis = result.get('last_analysis')
                if last_analysis:
                    print(f"         Type: {last_analysis.get('error_type', 'unknown')}")
                    if last_analysis.get('auto_fix'):
                        print(f"         Correction tentée: {last_analysis['auto_fix']}")
            else:
                print(f"      ⚠️  {result.get('error', 'Erreur')}")

    def on_agent_error(self, step_number: int, step: dict, error: dict):
        """Callback appelé en cas d'erreur dans l'agent"""
        print(f"\n⚠️  Erreur à l'étape {step_number}")
        print(f"    {error.get('error', 'Erreur inconnue')}")
