"""Interface terminal pour l'interaction avec l'IA"""

import sys
import os
from typing import Optional
from src.modules import OllamaClient, CommandParser, CommandExecutor, AutonomousAgent
from src.utils import (
    CommandLogger,
    InputValidator
)
from src.utils.tag_parser import TagParser
from src.security import SecurityValidator
from src.core import ShellEngine, ShellMode, HistoryManager, BuiltinCommands
from src.utils.command_helpers import CommandResultHandler, handle_command_errors
from src.terminal.display_manager import DisplayManager
from src.terminal.tag_display import TagDisplay
from src.terminal.rich_console import get_console
from src.terminal import rich_components
from config import prompts, project_templates, constants

class TerminalInterface:
    """Interface en ligne de commande pour le Terminal IA"""

    def __init__(self, settings, logger, cache_manager=None, user_config=None):
        """
        Initialise l'interface terminal

        Args:
            settings: Configuration de l'application
            logger: Logger principal
            cache_manager: Gestionnaire de cache optionnel (Phase 1)
            user_config: Gestionnaire de configuration utilisateur
        """
        self.settings = settings
        self.logger = logger
        self.cache_manager = cache_manager
        self.user_config = user_config
        self.running = False
        self.console = get_console()  # Console Rich unifiée

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
        self.input_validator = InputValidator()
        self.tag_display = TagDisplay(self.console)  # Affichage des balises IA
        self.tag_parser = TagParser()  # Parser de balises

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

            # Préchauffer le modèle pour éviter le timeout sur la première requête
            if settings.auto_warmup:
                self._warmup_ollama_model()

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
                'input_validator': self.input_validator,
                'user_config': self.user_config
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

    def _warmup_ollama_model(self):
        """
        Préchauffe le modèle Ollama pour éviter le timeout sur la première requête.

        Le premier appel à Ollama charge le modèle en mémoire, ce qui peut prendre
        90+ secondes. Cette méthode effectue une requête de warmup au démarrage
        pour que les vraies requêtes soient instantanées.
        """
        try:
            # Afficher un indicateur de chargement avec Rich
            with self.console.create_status("Chargement du modèle Ollama...") as status:
                # Requête minimale pour forcer le chargement du modèle
                warmup_prompt = "test"
                warmup_system = "Réponds seulement 'ok'"
                self.ollama.generate(warmup_prompt, system_prompt=warmup_system)

            self.logger.info("Modèle Ollama préchauffé avec succès")

        except Exception as e:
            # Ne pas bloquer le démarrage si le warmup échoue
            self.logger.warning(f"Échec du préchauffage Ollama: {e}")
            self.console.warning(f"Le préchauffage du modèle a échoué: {e}")

    def run(self):
        """Lance la boucle principale du terminal"""
        self.running = True

        # Afficher le banner avec Rich
        mode_name = self.shell_engine.mode_name.upper()
        self.console.print_banner(
            model=self.settings.ollama_model,
            host=self.settings.ollama_host,
            mode=mode_name,
            mode_description=self.shell_engine.get_mode_description()
        )

        # Vérifier la connexion à Ollama
        if not self.ollama.check_connection():
            warning_msg = f"Impossible de se connecter à Ollama!\n"
            warning_msg += f"Vérifiez que Ollama est lancé sur {self.settings.ollama_host}\n\n"
            warning_msg += "[dim]Vous pouvez continuer mais les commandes ne seront pas parsées.[/dim]"

            self.console.print(rich_components.create_warning_panel(warning_msg))

        # Boucle principale
        try:
            while self.running:
                self._process_input()
        except KeyboardInterrupt:
            self.console.print("\n")
            self.console.info("Interruption détectée...")
            self._quit()
        except Exception as e:
            self.logger.error(f"Erreur dans la boucle principale: {e}", exc_info=True)
            self.console.print()
            self.console.error(f"Erreur fatale: {e}")
            self._quit()

    def _process_input(self):
        """Traite une entrée utilisateur"""
        try:
            # Afficher le prompt avec Rich
            current_dir = self.executor.get_current_directory()
            mode_name = self.shell_engine.mode_name.upper()
            prompt_text = self.console.get_prompt_text(current_dir, mode_name)

            # Lire l'entrée utilisateur
            user_input = self.console.input(prompt_text).strip()

            if not user_input:
                return

            # Traiter la commande
            if user_input.startswith('/'):
                self._handle_special_command(user_input)
            else:
                self._handle_user_request(user_input)

        except EOFError:
            self.console.print("\n")
            self._quit()
        except KeyboardInterrupt:
            self.console.print("\n")
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
            self.console.print_help(prompts.HELP_TEXT)

        elif cmd_lower == '/manual':
            # Basculer en mode MANUAL
            if self.shell_engine.switch_to_manual():
                self.console.print()
                self.console.success("Mode MANUAL activé")
                self.console.print(f"[dim]{self.shell_engine.get_mode_description()}[/dim]")
            else:
                self.console.print()
                self.console.info("Déjà en mode MANUAL")

        elif cmd_lower == '/auto':
            # Basculer en mode AUTO
            if self.shell_engine.switch_to_auto():
                self.console.print()
                self.console.success("Mode AUTO activé")
                self.console.print(f"[dim]{self.shell_engine.get_mode_description()}[/dim]")
            else:
                self.console.print()
                self.console.info("Déjà en mode AUTO")

        elif cmd_lower == '/status':
            # Afficher le statut du shell
            self.display_manager.show_shell_status()

        elif cmd_lower == '/clear':
            self.parser.clear_history()
            self.ollama.clear_history()
            self.console.print()
            self.console.success("Historique effacé")

        elif cmd_lower == '/history':
            self.display_manager.show_history()

        elif cmd_lower == '/models' or cmd_lower == '/change':
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
                    self.console.print()
                    self.console.info("Usage: /agent <votre demande>")
                    self.console.print("[dim]Exemple: /agent crée-moi une API FastAPI[/dim]")
            else:
                self.console.print()
                self.console.error("Mode agent autonome désactivé")

        elif cmd_lower == '/pause':
            if self.agent and self.agent.is_running:
                self.agent.pause()
                self.console.print()
                self.console.print(prompts.AGENT_PAUSED)
            else:
                self.console.print()
                self.console.error("Aucun agent en cours d'exécution")

        elif cmd_lower == '/resume':
            if self.agent and self.agent.is_paused:
                self.agent.resume()
                self.console.print()
                self.console.success("Agent repris")
            else:
                self.console.print()
                self.console.error("Aucun agent en pause")

        elif cmd_lower == '/stop':
            if self.agent and self.agent.is_running:
                self.agent.stop()
                self.console.print()
                self.console.print(prompts.AGENT_STOPPED)
            else:
                self.console.print()
                self.console.error("Aucun agent en cours d'exécution")

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
                self.console.print()
                self.console.error("Commande cache inconnue")
                self.console.print("[dim]Usage: /cache [stats|clear][/dim]")

        elif cmd_lower == '/hardware':
            self.display_manager.show_hardware_info()

        elif cmd_lower.startswith('/rollback'):
            # Commandes de rollback (Phase 2)
            if not self.agent:
                self.console.print()
                self.console.error("Le mode agent n'est pas activé")
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
                self.console.print()
                self.console.error("Commande rollback inconnue")
                self.console.print("[dim]Usage: /rollback [list|restore|stats][/dim]")

        elif cmd_lower == '/security':
            # Commande de rapport de sécurité (Phase 2)
            self.display_manager.show_security_report()

        elif cmd_lower.startswith('/corrections'):
            # Commandes d'auto-correction (Phase 3)
            if not self.agent:
                self.console.print()
                self.console.error("Le mode agent n'est pas activé")
                return

            parts = command.split()
            if len(parts) == 1 or parts[1].lower() == 'stats':
                self.display_manager.show_correction_stats()
            elif parts[1].lower() == 'last':
                self.display_manager.show_last_error()
            else:
                self.console.print()
                self.console.error("Commande corrections inconnue")
                self.console.print("[dim]Usage: /corrections [stats|last][/dim]")

        else:
            self.console.print()
            self.console.error(f"Commande inconnue: {command}")
            self.console.print("[dim]Tapez /help pour voir les commandes disponibles[/dim]")

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
                self.console.print()
                self._handle_auto_mode(user_input)
                return

            # MODE AGENT : Toujours proposer le mode autonome
            elif self.shell_engine.is_agent_mode():
                self.console.print()
                self.console.info("Mode AGENT : Analyse en cours...")
                self._handle_autonomous_mode(user_input)
                return

        except Exception as e:
            self.logger.error(f"Erreur lors du traitement: {e}", exc_info=True)
            self.console.print()
            self.console.error(f"Erreur: {e}")

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

            # Callback pour afficher la sortie en temps réel
            def stream_output(line):
                """Affiche chaque ligne de sortie en temps réel"""
                self.console.print(f"[output]{line}[/output]")

            # Exécution avec streaming
            self.console.print()  # Ligne vide avant la sortie
            result = self.executor.execute_streaming(
                user_input,
                output_callback=stream_output,
                strict_mode=False
            )

            # Traiter le résultat via le handler unifié (display + history + logging)
            # skip_output=True car déjà affiché en temps réel
            self.result_handler.handle_result(
                result=result,
                command=user_input,
                user_input=user_input,
                mode="manual",
                skip_output=True
            )

        except Exception as e:
            self.logger.error(f"Erreur mode manuel: {e}", exc_info=True)
            self.console.error(f"Erreur: {e}")

    def _stream_ai_response_with_tags(self, user_input: str) -> dict:
        """
        Stream la réponse IA avec affichage des balises en temps réel

        Args:
            user_input: Demande utilisateur

        Returns:
            Dict avec command, explanation, risk_level, parsed_sections
        """
        self.console.print()  # Ligne vide avant

        # Obtenir le générateur de streaming
        stream_gen = self.parser.parse_user_request_stream(user_input)

        # Variables pour tracking des balises
        accumulated_text = ""
        current_tag = None
        tag_content = ""
        in_tag = False

        try:
            # Consommer le stream token par token
            for token in stream_gen:
                accumulated_text += token

                # Détecter les balises au fur et à mesure
                # Chercher les patterns [Tag] dans le texte accumulé
                if '[' in token:
                    in_tag = True

                if in_tag and ']' in token:
                    # Une balise vient d'être complétée, l'extraire
                    tag_match = accumulated_text.rfind('[')
                    if tag_match != -1:
                        tag_end = accumulated_text.find(']', tag_match)
                        if tag_end != -1:
                            # Balise détectée
                            potential_tag = accumulated_text[tag_match+1:tag_end]

                            # Si c'est une balise connue, afficher la section précédente
                            if self.tag_parser.is_known_tag(potential_tag):
                                # Afficher le contenu précédent si existant
                                if current_tag and tag_content.strip():
                                    self.tag_display.display_tag(current_tag, tag_content.strip())

                                # Nouvelle balise détectée
                                current_tag = potential_tag
                                tag_content = ""
                                in_tag = False
                                continue

                # Accumuler le contenu de la balise courante
                if current_tag and not in_tag:
                    tag_content += token
                elif not current_tag:
                    # Pas encore de balise, afficher brut
                    self.console.print(token, end="")

            # Afficher la dernière section si existante
            if current_tag and tag_content.strip():
                self.tag_display.display_tag(current_tag, tag_content.strip())

            self.console.print()  # Ligne vide après

            # Récupérer le résultat final du générateur
            try:
                result = stream_gen.gi_frame and stream_gen.send(None)
                if result is None:
                    # Le générateur n'a pas retourné de valeur, essayer la valeur de retour
                    result = getattr(stream_gen, 'gi_code', None)
            except StopIteration as e:
                result = e.value if hasattr(e, 'value') else None

            # Si pas de résultat, parser manuellement le texte accumulé
            if result is None:
                result = self.parser._process_ai_response(accumulated_text, user_input)

            return result

        except Exception as e:
            self.logger.error(f"Erreur lors du streaming: {e}", exc_info=True)
            self.console.error(f"Erreur streaming: {e}")

            # Fallback: parser le texte accumulé
            if accumulated_text:
                return self.parser._process_ai_response(accumulated_text, user_input)

            return {
                'command': None,
                'explanation': f"Erreur lors du streaming: {e}",
                'risk_level': 'unknown',
                'parsed_sections': {}
            }

    def _handle_auto_mode(self, user_input: str):
        """
        Gère les commandes en mode AUTO (avec IA)

        Args:
            user_input: Demande en langage naturel
        """
        try:
            # Si l'agent est activé, vérifier si c'est une demande complexe
            if self.agent and self.settings.agent_enabled:
                # Analyse de la complexité avec spinner
                with self.console.create_status("Analyse de la complexité...") as status:
                    analysis = self.agent.planner.analyze_request(user_input)

                if analysis.get('is_complex'):
                    # Demande complexe détectée, utiliser le mode agent
                    self.console.print()
                    self.console.info(f"Projet complexe détecté: {analysis.get('project_type')}")
                    self.console.info("Activation du mode agent autonome disponible")

                    # Demander si l'utilisateur veut utiliser le mode autonome
                    # PAS de spinner ici pour ne pas bloquer l'input()
                    response = input("\nUtiliser le mode agent autonome? (oui/non): ").strip().lower()
                    if response in ['oui', 'o', 'yes', 'y']:
                        self.shell_engine.switch_to_agent()
                        self._handle_autonomous_mode(user_input)
                        return
                    else:
                        self.console.warning("Mode agent annulé, traitement en mode commande simple")

            # Parser la demande avec streaming (affichage en temps réel avec balises)
            self.console.info("Analyse de votre demande...")
            parsed = self._stream_ai_response_with_tags(user_input)

            command = parsed.get('command')
            risk_level = parsed.get('risk_level', 'unknown')
            explanation = parsed.get('explanation', '')

            if not command:
                # Pas de commande générée - le message a déjà été affiché via les balises
                return

            # La commande a déjà été affichée via les balises [Commande]

            # Valider la sécurité
            is_valid, security_level, security_reason = self.security.validate_command(command)

            if not is_valid:
                self.console.print()
                self.console.error("Commande bloquée")
                self.console.print(f"   Raison: {security_reason}")
                self.logger.warning(f"Commande bloquée: {command} - {security_reason}")
                return

            # Demander confirmation si nécessaire
            if security_level == 'high' or risk_level == 'high':
                if not self._confirm_command(command, security_level, security_reason):
                    self.console.error("Commande annulée")
                    return

            # Exécuter la commande avec streaming
            self.console.info("Exécution...")
            self.console.print()  # Ligne vide avant la sortie

            # Callback pour afficher la sortie en temps réel
            def stream_output(line):
                """Affiche chaque ligne de sortie en temps réel"""
                self.console.print(f"[output]{line}[/output]")

            result = self.executor.execute_streaming(
                command,
                output_callback=stream_output,
                strict_mode=False
            )

            # Traiter le résultat (affichage + historique + logging)
            # skip_output=True car déjà affiché en temps réel
            self.result_handler.handle_result(
                result,
                command,
                user_input,
                "auto",
                skip_output=True
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
            self.console.error(f"Erreur: {e}")

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
            self.console.error("Mode agent non disponible")
            return

        try:
            print(prompts.AGENT_MODE_BANNER)
            print(prompts.AGENT_ANALYZING)

            # Analyser et générer le plan
            result = self.agent.execute_autonomous_task(user_request)

            if not result.get('success'):
                if result.get('reason') == 'not_complex':
                    self.console.info("Cette demande ne nécessite pas le mode autonome.")
                    self.console.print("   Elle sera traitée en mode commande simple.")
                    # Retourner au mode normal
                    return
                else:
                    self.console.error(result.get('message', 'Erreur inconnue'))
                    return

            # Afficher le plan
            plan = result.get('plan')
            if not plan:
                self.console.error("Impossible de générer un plan")
                return

            print("\n" + self.agent.planner.display_plan(plan))

            # Demander confirmation
            from rich.rule import Rule
            self.console.print(Rule(style="dim"))
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
                self.console.info("Fonctionnalité de modification du plan à venir...")
                self.console.print("   Pour l'instant, relancez avec une demande modifiée.")
            else:
                self.console.error("Exécution annulée")

        except KeyboardInterrupt:
            self.console.warning("Interruption détectée")
            if self.agent and self.agent.is_running:
                self.agent.stop()
                print(prompts.AGENT_STOPPED)
        except Exception as e:
            self.logger.error(f"Erreur mode autonome: {e}", exc_info=True)
            self.console.error(f"Erreur: {e}")

    def _quit(self):
        """Quitte l'application"""
        self.running = False
        print(prompts.GOODBYE_MESSAGE)
        self.logger.info("Terminal IA arrêté")
        sys.exit(0)
