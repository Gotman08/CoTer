"""Interface terminal pour l'interaction avec l'IA"""

import sys
import os
import requests
from typing import Optional
from simple_term_menu import TerminalMenu
from src.modules import OllamaClient, CommandParser, CommandExecutor, AutonomousAgent
from src.utils import (
    CommandLogger, SecurityValidator,
    StatsDisplayer, InputValidator, UIFormatter
)
from src.core import ShellEngine, ShellMode, HistoryManager, BuiltinCommands
from config import prompts, project_templates, constants

class TerminalInterface:
    """Interface en ligne de commande pour le Terminal IA"""

    def __init__(self, settings, logger, cache_manager=None):
        """
        Initialise l'interface terminal

        Args:
            settings: Configuration de l'application
            logger: Logger principal
            cache_manager: Gestionnaire de cache optionnel (Phase 1)
        """
        self.settings = settings
        self.logger = logger
        self.cache_manager = cache_manager
        self.running = False

        # Initialiser le moteur du shell hybride
        default_mode = ShellMode.MANUAL  # Mode par défaut: MANUAL
        self.shell_engine = ShellEngine(default_mode)
        self.logger.info(f"Shell initialisé en mode {default_mode.value}")

        # Initialiser le gestionnaire d'historique
        self.history_manager = HistoryManager()
        self.logger.info(f"Historique chargé: {len(self.history_manager)} commandes")

        # Initialiser les commandes builtins
        self.builtins = BuiltinCommands(self)
        self.logger.info(f"Commandes builtins chargées: {len(self.builtins.get_builtin_names())}")

        # Initialiser les utilitaires d'affichage (Refactoring)
        self.ui = UIFormatter()
        self.stats_displayer = StatsDisplayer(self.ui)
        self.input_validator = InputValidator()

        # Initialisation des composants
        self.logger.info("Initialisation des composants...")

        try:
            # Client Ollama (avec cache si disponible)
            self.ollama = OllamaClient(
                host=settings.ollama_host,
                model=settings.ollama_model,
                timeout=settings.ollama_timeout,
                logger=logger,
                cache_manager=cache_manager
            )

            # Parser de commandes
            self.parser = CommandParser(self.ollama, logger)

            # Exécuteur de commandes
            self.executor = CommandExecutor(settings, logger)

            # Validateur de sécurité
            self.security = SecurityValidator(logger)

            # Logger de commandes
            self.command_logger = CommandLogger(settings.logs_dir)

            # Agent autonome (si activé)
            self.agent = None
            if settings.agent_enabled:
                self.agent = AutonomousAgent(
                    self.ollama,
                    self.executor,
                    settings,
                    logger
                )
                # Configurer les callbacks
                self.agent.on_step_start = self._on_agent_step_start
                self.agent.on_step_complete = self._on_agent_step_complete
                self.agent.on_error = self._on_agent_error

            self.logger.info("Composants initialisés avec succès")

        except Exception as e:
            self.logger.error(f"Erreur lors de l'initialisation: {e}", exc_info=True)
            raise

    def run(self):
        """Lance la boucle principale du terminal"""
        self.running = True

        # Afficher le logo ASCII
        print(prompts.ASCII_LOGO)
        print(f"\nModèle: {self.settings.ollama_model} | Host: {self.settings.ollama_host}")

        # Afficher le mode actuel
        mode_symbol = self.shell_engine.get_prompt_symbol()
        mode_name = self.shell_engine.mode_name.upper()
        print(f"{mode_symbol}  Mode: {mode_name} - {self.shell_engine.get_mode_description()}")

        print("\nCommandes: /manual /auto /agent /help /quit")
        print("Tapez /help pour l'aide complète\n")

        # Vérifier la connexion à Ollama
        if not self.ollama.check_connection():
            print("⚠️  ATTENTION: Impossible de se connecter à Ollama!")
            print(f"   Vérifiez que Ollama est lancé sur {self.settings.ollama_host}")
            print("   Vous pouvez continuer mais les commandes ne seront pas parsées.\n")

        # Boucle principale
        try:
            while self.running:
                self._process_input()
        except KeyboardInterrupt:
            print("\n\nInterruption détectée...")
            self._quit()
        except Exception as e:
            self.logger.error(f"Erreur dans la boucle principale: {e}", exc_info=True)
            print(f"\n❌ Erreur fatale: {e}")
            self._quit()

    def _process_input(self):
        """Traite une entrée utilisateur"""
        try:
            # Afficher le prompt avec le symbole du mode actuel et le répertoire courant
            current_dir = self.executor.get_current_directory()
            mode_symbol = self.shell_engine.get_prompt_symbol()
            prompt_text = f"\n{mode_symbol} [{current_dir}]\n> "

            # Lire l'entrée utilisateur
            user_input = input(prompt_text).strip()

            if not user_input:
                return

            # Traiter la commande
            if user_input.startswith('/'):
                self._handle_special_command(user_input)
            else:
                self._handle_user_request(user_input)

        except EOFError:
            print("\n")
            self._quit()
        except KeyboardInterrupt:
            print("\n")
            raise

    def _handle_special_command(self, command: str):
        """
        Gère les commandes spéciales

        Args:
            command: Commande spéciale (commence par /)
        """
        cmd_lower = command.lower()

        if cmd_lower == '/quit' or cmd_lower == '/exit':
            self._quit()

        elif cmd_lower == '/help':
            print(prompts.HELP_TEXT)

        elif cmd_lower == '/manual':
            # Basculer en mode MANUAL
            if self.shell_engine.switch_to_manual():
                print(f"\n⌨️  Mode MANUAL activé")
                print(f"   {self.shell_engine.get_mode_description()}")
            else:
                print(f"\n⌨️  Déjà en mode MANUAL")

        elif cmd_lower == '/auto':
            # Basculer en mode AUTO
            if self.shell_engine.switch_to_auto():
                print(f"\n🤖 Mode AUTO activé")
                print(f"   {self.shell_engine.get_mode_description()}")
            else:
                print(f"\n🤖 Déjà en mode AUTO")

        elif cmd_lower == '/status':
            # Afficher le statut du shell
            self._show_shell_status()

        elif cmd_lower == '/clear':
            self.parser.clear_history()
            self.ollama.clear_history()
            print("✅ Historique effacé")

        elif cmd_lower == '/history':
            self._show_history()

        elif cmd_lower == '/models':
            self._list_models()

        elif cmd_lower == '/info':
            self._show_system_info()

        elif cmd_lower == '/templates':
            self._list_templates()

        elif cmd_lower.startswith('/agent'):
            # Mode agent autonome
            if self.agent:
                # Basculer en mode AGENT
                self.shell_engine.switch_to_agent()

                # Extraire la demande après /agent
                request = command[6:].strip()
                if request:
                    self._handle_autonomous_mode(request)
                else:
                    print("Usage: /agent <votre demande>")
                    print("Exemple: /agent crée-moi une API FastAPI")
            else:
                print("❌ Mode agent autonome désactivé")

        elif cmd_lower == '/pause':
            if self.agent and self.agent.is_running:
                self.agent.pause()
                print(prompts.AGENT_PAUSED)
            else:
                print("❌ Aucun agent en cours d'exécution")

        elif cmd_lower == '/resume':
            if self.agent and self.agent.is_paused:
                self.agent.resume()
                print("▶️  Agent repris")
            else:
                print("❌ Aucun agent en pause")

        elif cmd_lower == '/stop':
            if self.agent and self.agent.is_running:
                self.agent.stop()
                print(prompts.AGENT_STOPPED)
            else:
                print("❌ Aucun agent en cours d'exécution")

        elif cmd_lower.startswith('/cache'):
            # Commandes de gestion du cache (Phase 1)
            parts = command.split()
            if len(parts) == 1:
                # /cache seul = afficher stats
                self._show_cache_stats()
            elif parts[1].lower() == 'stats':
                self._show_cache_stats()
            elif parts[1].lower() == 'clear':
                self._clear_cache()
            else:
                print("❌ Commande cache inconnue")
                print("Usage: /cache [stats|clear]")

        elif cmd_lower == '/hardware':
            self._show_hardware_info()

        elif cmd_lower.startswith('/rollback'):
            # Commandes de rollback (Phase 2)
            if not self.agent:
                print("❌ Le mode agent n'est pas activé")
                return

            parts = command.split()
            if len(parts) == 1:
                # /rollback seul = afficher snapshots disponibles
                self._show_snapshots()
            elif parts[1].lower() == 'list':
                self._show_snapshots()
            elif parts[1].lower() == 'restore':
                # /rollback restore [snapshot_id]
                snapshot_id = parts[2] if len(parts) > 2 else None
                self._restore_snapshot(snapshot_id)
            elif parts[1].lower() == 'stats':
                self._show_rollback_stats()
            else:
                print("❌ Commande rollback inconnue")
                print("Usage: /rollback [list|restore|stats]")

        elif cmd_lower == '/security':
            # Commande de rapport de sécurité (Phase 2)
            self._show_security_report()

        elif cmd_lower.startswith('/corrections'):
            # Commandes d'auto-correction (Phase 3)
            if not self.agent:
                print("❌ Le mode agent n'est pas activé")
                return

            parts = command.split()
            if len(parts) == 1 or parts[1].lower() == 'stats':
                self._show_correction_stats()
            elif parts[1].lower() == 'last':
                self._show_last_error()
            else:
                print("❌ Commande corrections inconnue")
                print("Usage: /corrections [stats|last]")

        else:
            print(f"❌ Commande inconnue: {command}")
            print("   Tapez /help pour voir les commandes disponibles")

    def _handle_user_request(self, user_input: str):
        """
        Gère une demande utilisateur normale

        Args:
            user_input: Demande de l'utilisateur
        """
        # Incrémenter le compteur de commandes
        self.shell_engine.increment_command_count()

        try:
            # MODE MANUAL : Exécution directe sans IA
            if self.shell_engine.is_manual_mode():
                self._handle_manual_mode(user_input)
                return

            # MODE AUTO : Parsing IA puis exécution
            elif self.shell_engine.is_auto_mode():
                print(f"\n🔄 Analyse de votre demande...")
                self._handle_auto_mode(user_input)
                return

            # MODE AGENT : Toujours proposer le mode autonome
            elif self.shell_engine.is_agent_mode():
                print(f"\n🏗️  Mode AGENT : Analyse en cours...")
                self._handle_autonomous_mode(user_input)
                return

        except Exception as e:
            self.logger.error(f"Erreur lors du traitement: {e}", exc_info=True)
            print(f"\n❌ Erreur: {e}")

    def _handle_manual_mode(self, user_input: str):
        """
        Gère les commandes en mode MANUAL (exécution directe)

        Args:
            user_input: Commande shell à exécuter
        """
        try:
            # Vérifier si c'est une commande builtin
            if self.builtins.is_builtin(user_input):
                result = self.builtins.execute(user_input)
                if result is None:
                    # Pas vraiment builtin, passer à l'exécution normale
                    pass
                else:
                    # Commande builtin exécutée
                    # Afficher le résultat
                    self._display_result(result)

                    # Ajouter à l'historique persistant
                    self.history_manager.add_command(
                        command=user_input,
                        mode="manual",
                        success=result['success']
                    )

                    # Logger la commande
                    self.command_logger.log_command(
                        user_input=user_input,
                        command=user_input,
                        success=result['success'],
                        output=result.get('output', ''),
                        error=result.get('error', '')
                    )
                    return

            # Exécuter via subprocess (pas builtin)
            # strict_mode=False pour autoriser pipes, redirections, etc.
            result = self.executor.execute(user_input, strict_mode=False)

            # Afficher le résultat
            self._display_result(result)

            # Ajouter à l'historique persistant
            self.history_manager.add_command(
                command=user_input,
                mode="manual",
                success=result['success']
            )

            # Logger la commande
            self.command_logger.log_command(
                user_input=user_input,
                command=user_input,  # En mode manual, la commande = l'input
                success=result['success'],
                output=result.get('output', ''),
                error=result.get('error', '')
            )

        except Exception as e:
            self.logger.error(f"Erreur mode manuel: {e}", exc_info=True)
            print(f"\n❌ Erreur: {e}")

    def _handle_auto_mode(self, user_input: str):
        """
        Gère les commandes en mode AUTO (avec IA)

        Args:
            user_input: Demande en langage naturel
        """
        try:
            # Si l'agent est activé, vérifier si c'est une demande complexe
            if self.agent and self.settings.agent_enabled:
                analysis = self.agent.planner.analyze_request(user_input)

                if analysis.get('is_complex'):
                    # Demande complexe détectée, utiliser le mode agent
                    print(f"\n📦 Projet complexe détecté: {analysis.get('project_type')}")
                    print("🤖 Activation du mode agent autonome...")

                    # Demander si l'utilisateur veut utiliser le mode autonome
                    response = input("\nUtiliser le mode agent autonome? (oui/non): ").strip().lower()
                    if response in ['oui', 'o', 'yes', 'y']:
                        self.shell_engine.switch_to_agent()
                        self._handle_autonomous_mode(user_input)
                        return
                    else:
                        print("Mode agent annulé, traitement en mode commande simple.")

            # Parser la demande en mode normal
            parsed = self.parser.parse_user_request(user_input)

            command = parsed.get('command')
            risk_level = parsed.get('risk_level', 'unknown')
            explanation = parsed.get('explanation', '')

            if not command:
                print(f"\n💬 {explanation}")
                return

            # Afficher la commande générée
            print(f"\n📝 Commande générée: {command}")

            # Valider la sécurité
            is_valid, security_level, security_reason = self.security.validate_command(command)

            if not is_valid:
                print(f"\n🚫 Commande bloquée!")
                print(f"   Raison: {security_reason}")
                self.logger.warning(f"Commande bloquée: {command} - {security_reason}")
                return

            # Demander confirmation si nécessaire
            if security_level == 'high' or risk_level == 'high':
                if not self._confirm_command(command, security_level, security_reason):
                    print("❌ Commande annulée")
                    return

            # Exécuter la commande
            print(f"\n⚙️  Exécution...")
            result = self.executor.execute(command)

            # Afficher le résultat
            self._display_result(result)

            # Ajouter à l'historique persistant
            self.history_manager.add_command(
                command=command,
                mode="auto",
                success=result['success']
            )

            # Logger la commande
            self.command_logger.log_command(
                user_input=user_input,
                command=command,
                success=result['success'],
                output=result.get('output', ''),
                error=result.get('error', '')
            )

            # Phase 2: Enregistrer dans l'historique de sécurité
            self.security.record_command_execution(
                command=command,
                success=result['success'],
                risk_level=security_level
            )

            # Ajouter à l'historique du parser (legacy)
            self.parser.add_to_history(user_input, command, result.get('output', ''))

        except Exception as e:
            self.logger.error(f"Erreur mode auto: {e}", exc_info=True)
            print(f"\n❌ Erreur: {e}")

    def _confirm_command(self, command: str, risk_level: str, reason: str) -> bool:
        """
        Demande confirmation pour une commande à risque

        Args:
            command: La commande à confirmer
            risk_level: Niveau de risque
            reason: Raison du risque

        Returns:
            True si l'utilisateur confirme
        """
        message = self.security.get_confirmation_message(command, risk_level, reason)
        print(message)

        while True:
            response = input("\nVotre réponse (oui/non): ").strip().lower()
            if response in ['oui', 'o', 'yes', 'y']:
                return True
            elif response in ['non', 'n', 'no']:
                return False
            else:
                print("Réponse invalide. Tapez 'oui' ou 'non'")

    def _display_result(self, result: dict):
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

    def _show_history(self):
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

    def _list_models(self):
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

    def _show_system_info(self):
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

    def _list_templates(self):
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

    def _handle_autonomous_mode(self, user_request: str):
        """
        Gère une demande en mode agent autonome

        Args:
            user_request: Demande utilisateur
        """
        if not self.agent:
            print("❌ Mode agent non disponible")
            return

        try:
            print(prompts.AGENT_MODE_BANNER)
            print(prompts.AGENT_ANALYZING)

            # Analyser et générer le plan
            result = self.agent.execute_autonomous_task(user_request)

            if not result.get('success'):
                if result.get('reason') == 'not_complex':
                    print("\n💡 Cette demande ne nécessite pas le mode autonome.")
                    print("   Elle sera traitée en mode commande simple.")
                    # Retourner au mode normal
                    return
                else:
                    print(f"\n❌ Erreur: {result.get('message', 'Erreur inconnue')}")
                    return

            # Afficher le plan
            plan = result.get('plan')
            if not plan:
                print("❌ Impossible de générer un plan")
                return

            print("\n" + self.agent.planner.display_plan(plan))

            # Demander confirmation
            print("\n" + "═" * 60)
            response = input("\nVoulez-vous lancer l'exécution? (oui/non/modifier): ").strip().lower()

            if response in ['oui', 'o', 'yes', 'y']:
                # Lancer l'exécution
                print(prompts.AGENT_EXECUTING)

                exec_result = self.agent.execute_plan(plan)

                if exec_result.get('success'):
                    print(prompts.AGENT_COMPLETED)
                    print(f"\n✨ Projet créé dans: {exec_result.get('project_path')}")

                    # Afficher résumé
                    results = exec_result.get('results', [])
                    print(f"\n📊 Résumé: {len(results)} étapes exécutées")

                elif exec_result.get('stopped'):
                    print(prompts.AGENT_STOPPED)
                else:
                    print(prompts.AGENT_ERROR)
                    print(f"Erreur: {exec_result.get('error', 'Erreur inconnue')}")

            elif response in ['modifier', 'm', 'mod']:
                print("\n💡 Fonctionnalité de modification du plan à venir...")
                print("   Pour l'instant, relancez avec une demande modifiée.")
            else:
                print("\n❌ Exécution annulée")

        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption détectée")
            if self.agent and self.agent.is_running:
                self.agent.stop()
                print(prompts.AGENT_STOPPED)
        except Exception as e:
            self.logger.error(f"Erreur mode autonome: {e}", exc_info=True)
            print(f"\n❌ Erreur: {e}")

    def _on_agent_step_start(self, step_number: int, step: dict):
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

    def _on_agent_step_complete(self, step_number: int, step: dict, result: dict):
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

    def _on_agent_error(self, step_number: int, step: dict, error: dict):
        """Callback appelé en cas d'erreur dans l'agent"""
        print(f"\n⚠️  Erreur à l'étape {step_number}")
        print(f"    {error.get('error', 'Erreur inconnue')}")

    def _show_cache_stats(self):
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

    def _clear_cache(self):
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

    def _show_hardware_info(self):
        """Affiche les informations hardware et optimisations"""
        from src.utils import HardwareOptimizer

        print("\n" + "="*60)
        print("🖥️  INFORMATIONS HARDWARE")
        print("="*60)

        try:
            optimizer = HardwareOptimizer(self.logger)
            print(optimizer.get_optimization_report())
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des infos hardware: {e}")
            self.logger.error(f"Erreur hardware info: {e}")

    def _show_snapshots(self):
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

    def _restore_snapshot(self, snapshot_id: Optional[str] = None):
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

    def _show_rollback_stats(self):
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

    def _show_security_report(self):
        """Affiche le rapport de sécurité"""
        try:
            report = self.security.get_security_report()
            self.stats_displayer.display_security_report(report)
        except Exception as e:
            self.ui.print_error(f"Erreur: {e}")
            self.logger.error(f"Erreur rapport sécurité: {e}")

    def _show_correction_stats(self):
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

    def _show_last_error(self):
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

    def _show_shell_status(self):
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

    def _quit(self):
        """Quitte l'application"""
        self.running = False
        print(prompts.GOODBYE_MESSAGE)
        self.logger.info("Terminal IA arrêté")
        sys.exit(0)
