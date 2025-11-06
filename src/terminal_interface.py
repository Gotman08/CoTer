"""Interface terminal pour l'interaction avec l'IA"""

import sys
import os
from typing import Optional
from src.modules import OllamaClient, CommandParser, CommandExecutor, AutonomousAgent
from src.utils import (
    CommandLogger,
    StatsDisplayer, InputValidator, UIFormatter
)
from src.security import SecurityValidator
from src.core import ShellEngine, ShellMode, HistoryManager, BuiltinCommands
from src.utils.command_helpers import CommandResultHandler, handle_command_errors
from src.terminal.display_manager import DisplayManager
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

        # Initialiser le gestionnaire de résultats unifié (Refactoring Phase 1.3)
        self.result_handler = CommandResultHandler(self)

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

            # Initialiser le DisplayManager avec tous les composants
            components = {
                'settings': self.settings,
                'logger': self.logger,
                'shell_engine': self.shell_engine,
                'security': self.security,
                'history_manager': self.history_manager,
                'ollama': self.ollama,
                'executor': self.executor,
                'cache_manager': self.cache_manager,
                'agent': self.agent,
                'ui': self.ui,
                'stats_displayer': self.stats_displayer,
                'input_validator': self.input_validator
            }
            self.display_manager = DisplayManager(components)

            # Configurer les callbacks de l'agent (si activé)
            if self.agent:
                self.agent.on_step_start = self.display_manager.on_agent_step_start
                self.agent.on_step_complete = self.display_manager.on_agent_step_complete
                self.agent.on_error = self.display_manager.on_agent_error

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
            self.display_manager.show_shell_status()

        elif cmd_lower == '/clear':
            self.parser.clear_history()
            self.ollama.clear_history()
            print("✅ Historique effacé")

        elif cmd_lower == '/history':
            self.display_manager.show_history()

        elif cmd_lower == '/models':
            self.display_manager.list_models()

        elif cmd_lower == '/info':
            self.display_manager.show_system_info()

        elif cmd_lower == '/templates':
            self.display_manager.list_templates()

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
                self.display_manager.show_cache_stats()
            elif parts[1].lower() == 'stats':
                self.display_manager.show_cache_stats()
            elif parts[1].lower() == 'clear':
                self.display_manager.clear_cache()
            else:
                print("❌ Commande cache inconnue")
                print("Usage: /cache [stats|clear]")

        elif cmd_lower == '/hardware':
            self.display_manager.show_hardware_info()

        elif cmd_lower.startswith('/rollback'):
            # Commandes de rollback (Phase 2)
            if not self.agent:
                print("❌ Le mode agent n'est pas activé")
                return

            parts = command.split()
            if len(parts) == 1:
                # /rollback seul = afficher snapshots disponibles
                self.display_manager.show_snapshots()
            elif parts[1].lower() == 'list':
                self.display_manager.show_snapshots()
            elif parts[1].lower() == 'restore':
                # /rollback restore [snapshot_id]
                snapshot_id = parts[2] if len(parts) > 2 else None
                self.display_manager.restore_snapshot(snapshot_id)
            elif parts[1].lower() == 'stats':
                self.display_manager.show_rollback_stats()
            else:
                print("❌ Commande rollback inconnue")
                print("Usage: /rollback [list|restore|stats]")

        elif cmd_lower == '/security':
            # Commande de rapport de sécurité (Phase 2)
            self.display_manager.show_security_report()

        elif cmd_lower.startswith('/corrections'):
            # Commandes d'auto-correction (Phase 3)
            if not self.agent:
                print("❌ Le mode agent n'est pas activé")
                return

            parts = command.split()
            if len(parts) == 1 or parts[1].lower() == 'stats':
                self.display_manager.show_correction_stats()
            elif parts[1].lower() == 'last':
                self.display_manager.show_last_error()
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
                if result is not None:
                    # Commande builtin exécutée - utiliser le handler unifié
                    self.result_handler.handle_result(
                        result=result,
                        command=user_input,
                        user_input=user_input,
                        mode="manual"
                    )
                    return

            # Exécuter via subprocess (pas builtin)
            # strict_mode=False pour autoriser pipes, redirections, etc.
            result = self.executor.execute(user_input, strict_mode=False)

            # Traiter le résultat via le handler unifié (display + history + logging)
            self.result_handler.handle_result(
                result=result,
                command=user_input,
                user_input=user_input,
                mode="manual"
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

            # Traiter le résultat (affichage + historique + logging)
            self.result_handler.handle_result(result, command, user_input, "auto")

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

    def _quit(self):
        """Quitte l'application"""
        self.running = False
        print(prompts.GOODBYE_MESSAGE)
        self.logger.info("Terminal IA arrêté")
        sys.exit(0)
