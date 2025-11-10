"""
Handler pour les différents modes d'exécution (MANUAL, AUTO, FAST, AGENT)

Extrait de terminal_interface.py pour réduire la complexité
et séparer les responsabilités.
"""

from typing import TYPE_CHECKING, Callable, Optional
from config import prompts
from config.constants import MAX_AUTO_ITERATIONS

if TYPE_CHECKING:
    from src.terminal_interface import TerminalInterface


class ModeHandler:
    """
    Gère l'exécution des commandes dans les différents modes.

    Modes supportés:
    - MANUAL: Exécution directe sans IA
    - AUTO: Parsing IA itératif avec boucle
    - FAST: Parsing IA one-shot (une commande)
    - AGENT: Mode autonome avec planification

    Attributes:
        terminal: Référence vers l'instance TerminalInterface parente
    """

    def __init__(self, terminal: 'TerminalInterface'):
        """
        Initialise le gestionnaire de modes.

        Args:
            terminal: Instance de TerminalInterface pour accéder aux composants
        """
        self.terminal = terminal
        self.console = terminal.console
        self.logger = terminal.logger
        self.settings = terminal.settings
        self.executor = terminal.executor
        self.parser = terminal.parser
        self.ollama = terminal.ollama
        self.security = terminal.security
        self.agent = terminal.agent
        self.shell_engine = terminal.shell_engine
        self.result_handler = terminal.result_handler

    def handle_user_request(self, user_input: str) -> None:
        """
        Route une demande utilisateur vers le mode approprié.

        Args:
            user_input: Demande de l'utilisateur
        """
        # Incrémenter le compteur de commandes
        self.shell_engine.increment_command_count()

        try:
            # MODE MANUAL : Exécution directe sans IA
            if self.shell_engine.is_manual_mode():
                self.handle_manual_mode(user_input)
                return

            # MODE AUTO : Parsing IA itératif avec boucle
            elif self.shell_engine.is_auto_mode():
                self.console.print()
                self.handle_auto_mode(user_input)
                return

            # MODE FAST : Parsing IA one-shot (une commande et c'est fini)
            elif self.shell_engine.is_fast_mode():
                self.console.print()
                self.handle_fast_mode(user_input)
                return

            # MODE AGENT : Toujours proposer le mode autonome
            elif self.shell_engine.is_agent_mode():
                self.console.print()
                self.console.info("Mode AGENT : Analyse en cours...")
                self.terminal._handle_autonomous_mode(user_input)
                return

        except Exception as error:
            self.logger.error(f"Erreur lors du traitement: {error}", exc_info=True)
            self.console.print()
            self.console.error(f"Erreur: {error}")

    # ═══════════════════════════════════════════════════════════════
    # MODE MANUAL
    # ═══════════════════════════════════════════════════════════════

    def handle_manual_mode(self, user_input: str) -> None:
        """
        Gère les commandes en mode MANUAL (exécution directe sans IA).

        Args:
            user_input: Commande shell à exécuter
        """
        try:
            # Vérifier si c'est une commande builtin
            if self.terminal.builtins.is_builtin(user_input):
                result = self.terminal.builtins.execute(user_input)
                if result is not None:
                    # Commande builtin exécutée - utiliser le handler unifié
                    self.result_handler.handle_result(
                        result=result,
                        command=user_input,
                        user_input=user_input,
                        mode="manual"
                    )
                    return

            # Callback pour afficher la sortie en temps réel
            def stream_output(line: str) -> None:
                """Affiche chaque ligne de sortie en temps réel"""
                self.console.print(f"[output]{line}[/output]")

            # Exécution avec shell PTY
            self.console.print()  # Ligne vide avant la sortie
            result = self.executor.execute_pty(
                user_input,
                output_callback=stream_output
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

        except Exception as error:
            self.logger.error(f"Erreur mode manuel: {error}", exc_info=True)
            self.console.error(f"Erreur: {error}")

    # ═══════════════════════════════════════════════════════════════
    # MODE FAST
    # ═══════════════════════════════════════════════════════════════

    def handle_fast_mode(self, user_input: str) -> None:
        """
        Gère les commandes en mode FAST (IA one-shot, pas de boucle itérative).

        Args:
            user_input: Demande en langage naturel
        """
        self.logger.info(f"Entrée en mode FAST one-shot - Demande: {user_input[:100]}...")
        try:
            # Parser la demande avec streaming
            self.console.info("⚡ Mode FAST - Génération d'une commande optimale...")

            # Temporairement changer le prompt système pour mode FAST
            from config.prompts import SYSTEM_PROMPT_FAST
            original_prompt = self.parser._get_parsing_system_prompt

            # Override temporaire de la méthode pour utiliser SYSTEM_PROMPT_FAST
            self.parser._get_parsing_system_prompt = lambda: SYSTEM_PROMPT_FAST

            try:
                ai_response = self.terminal._stream_ai_response_with_tags(user_input)
            finally:
                # Restaurer le prompt original
                self.parser._get_parsing_system_prompt = original_prompt

            command = ai_response.get('command')
            risk_level = ai_response.get('risk_level', 'unknown')
            explanation = ai_response.get('explanation', '')

            if not command:
                # Pas de commande générée
                return

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
                if not self.terminal._confirm_command(command, security_level, security_reason):
                    self.console.error("Commande annulée")
                    return

            # Exécuter la commande avec streaming
            self.console.info("Exécution...")
            self.console.print()  # Ligne vide avant la sortie

            # Callback pour afficher la sortie en temps réel
            def stream_output(line: str) -> None:
                """Affiche chaque ligne de sortie en temps réel"""
                self.console.print(f"[output]{line}[/output]")

            result = self.executor.execute_streaming(
                command,
                output_callback=stream_output,
                strict_mode=False
            )

            # Traiter le résultat
            self.result_handler.handle_result(
                result,
                command,
                user_input,
                "fast",
                skip_output=True
            )

            # Enregistrer dans l'historique de sécurité
            self.security.record_command_execution(
                command=command,
                success=result['success'],
                risk_level=security_level
            )

            # Ajouter à l'historique du parser
            self.parser.add_to_history(user_input, command, result.get('output', ''))

            self.logger.info(f"Fin du mode FAST one-shot - Commande: {command}")

        except Exception as error:
            self.logger.error(f"Erreur mode fast: {error}", exc_info=True)
            self.console.error(f"Erreur: {error}")

    # ═══════════════════════════════════════════════════════════════
    # MODE AUTO
    # ═══════════════════════════════════════════════════════════════

    def handle_auto_mode(self, user_input: str) -> None:
        """
        Gère les commandes en mode AUTO (avec IA - MODE ITÉRATIF).
        Boucle itérative : commande → résultat → IA décide prochaine étape

        Args:
            user_input: Demande en langage naturel
        """
        self.logger.info(f"Entrée en mode AUTO itératif - Demande: {user_input[:100]}...")
        try:
            # Vérifier si la planification en arrière-plan est disponible
            if self._try_background_planning(user_input):
                return  # Plan exécuté avec succès

            # BOUCLE ITÉRATIVE
            context_history = []  # Historique des commandes et résultats
            step_number = 0
            self.logger.info(f"Démarrage de la boucle itérative (max {MAX_AUTO_ITERATIONS} étapes)")

            while step_number < MAX_AUTO_ITERATIONS:
                step_number += 1
                self.logger.debug(f"Itération {step_number}/{MAX_AUTO_ITERATIONS}")
                self.console.print()
                self.console.info(f"🔄 Étape {step_number}/{MAX_AUTO_ITERATIONS}")

                # Générer la commande suivante avec l'IA
                ai_response = self._generate_next_command(user_input, context_history)

                command = ai_response.get('command')
                risk_level = ai_response.get('risk_level', 'unknown')
                explanation = ai_response.get('explanation', '')

                self.logger.info(f"Commande générée: {command}")
                self.logger.debug(f"Risk level: {risk_level}, Explication: {explanation[:100]}...")

                if not command:
                    # Pas de commande générée
                    self.logger.warning("Aucune commande générée par l'IA")
                    self.console.warning("Aucune commande générée")
                    break

                # Valider et exécuter la commande
                execution_result = self._validate_and_execute_command(
                    command, user_input, risk_level
                )

                if execution_result is None:
                    # Commande bloquée ou annulée
                    break

                # Ajouter au contexte itératif
                context_history.append({
                    'command': command,
                    'output': execution_result.get('output', ''),
                    'success': execution_result['success']
                })
                self.logger.debug(f"Contexte mis à jour: {len(context_history)} étapes au total")

                # Détecter si la tâche est complétée
                if self.terminal._is_task_completed(explanation):
                    self.logger.info("Tâche détectée comme complétée par l'IA")
                    self.console.print()
                    self.console.success("✓ Tâche complétée!")
                    break

                # Demander à l'utilisateur s'il veut continuer
                user_choice = self.terminal._prompt_next_action_with_arrows()
                self.logger.info(f"Choix utilisateur: {user_choice}")

                if user_choice == "stop":
                    self.logger.info("Arrêt de la boucle itérative demandé par l'utilisateur")
                    self.console.info("Arrêt demandé par l'utilisateur")
                    break
                elif user_choice == "improve":
                    # Demander des précisions supplémentaires
                    improvement = input("\n💬 Que voulez-vous préciser/améliorer ? ").strip()
                    if improvement:
                        self.logger.info(f"Précision utilisateur ajoutée: {improvement[:100]}...")
                        user_input = f"{user_input}\n\nPrécision: {improvement}"
                        self.console.success("Précision prise en compte")
                    continue
                elif user_choice == "continue":
                    # Continuer l'itération
                    self.logger.debug("Utilisateur a choisi de continuer")
                    continue

            # Fin de la boucle
            if step_number >= MAX_AUTO_ITERATIONS:
                self.logger.warning(f"Limite de {MAX_AUTO_ITERATIONS} itérations atteinte")
                self.console.warning(f"⚠️  Limite de {MAX_AUTO_ITERATIONS} itérations atteinte")

            self.logger.info(f"Fin du mode AUTO itératif - {step_number} étapes exécutées")

        except KeyboardInterrupt:
            self.logger.info("Interruption par l'utilisateur (Ctrl+C) en mode AUTO")
            self.console.print()
            self.console.warning("Interruption par l'utilisateur (Ctrl+C)")
        except Exception as error:
            self.logger.error(f"Erreur mode auto: {error}", exc_info=True)
            self.console.error(f"Erreur: {error}")

    # ═══════════════════════════════════════════════════════════════
    # MÉTHODES PRIVÉES - MODE AUTO
    # ═══════════════════════════════════════════════════════════════

    def _try_background_planning(self, user_input: str) -> bool:
        """
        Tente d'utiliser la planification en arrière-plan si disponible.

        Args:
            user_input: Demande utilisateur

        Returns:
            True si un plan a été exécuté avec succès, False sinon
        """
        if not self.terminal.background_planner or not self.terminal.background_planner.is_running:
            return False

        # Envoyer la requête pour analyse en arrière-plan
        self.terminal.background_planner.analyze_request_async(user_input)
        self.logger.debug("Requête envoyée au planificateur en arrière-plan")

        # Vérifier si un plan est déjà disponible
        import time
        time.sleep(0.1)  # Petit délai pour laisser l'analyse démarrer

        # Récupérer le dernier plan disponible
        latest_plan = self.terminal.background_planner.get_latest_plan()
        latest_analysis = self.terminal.background_planner.get_latest_analysis()

        # Si un plan complexe est disponible et auto-exécution activée
        if (latest_plan and latest_analysis and
            latest_analysis.get('is_complex') and
            getattr(self.settings, 'background_planning_auto_execute', True)):

            self.console.print()
            self.console.info("🎯 Plan détecté pour cette requête")

            # Exécuter le plan automatiquement
            self.logger.info("Exécution automatique du plan en arrière-plan")

            exec_result = self.agent.execute_plan(latest_plan)

            if exec_result.get('success'):
                self.console.success("✓ Plan exécuté avec succès!")

                # Marquer comme exécuté dans le stockage
                if self.terminal.plan_storage:
                    request_id = latest_plan.get('_metadata', {}).get('request_id')
                    if request_id:
                        recent_plans = self.terminal.plan_storage.get_recent_plans(limit=1)
                        if recent_plans:
                            self.terminal.plan_storage.mark_executed(recent_plans[0]['id'], 'success')

                return True
            else:
                self.console.warning("⚠️  Le plan a échoué, passage en mode itératif")

        return False

    def _generate_next_command(self, user_input: str, context_history: list) -> dict:
        """
        Génère la prochaine commande avec l'IA en fonction du contexte.

        Args:
            user_input: Demande utilisateur initiale
            context_history: Historique des étapes précédentes

        Returns:
            Réponse IA avec command, explanation, risk_level
        """
        if context_history:
            # Avec historique (étapes > 1)
            self.logger.debug(f"Génération avec historique ({len(context_history)} étapes précédentes)")
            return self.terminal._stream_ai_response_with_history(user_input, context_history)
        else:
            # Première étape, pas d'historique
            self.logger.debug("Première génération (sans historique)")
            self.console.info("Analyse de votre demande...")
            return self.terminal._stream_ai_response_with_tags(user_input)

    def _validate_and_execute_command(
        self,
        command: str,
        user_input: str,
        risk_level: str
    ) -> Optional[dict]:
        """
        Valide et exécute une commande générée par l'IA.

        Args:
            command: Commande à exécuter
            user_input: Demande utilisateur originale
            risk_level: Niveau de risque de la commande

        Returns:
            Résultat d'exécution ou None si bloqué/annulé
        """
        # Valider la sécurité
        is_valid, security_level, security_reason = self.security.validate_command(command)

        if not is_valid:
            self.console.print()
            self.console.error("Commande bloquée")
            self.console.print(f"   Raison: {security_reason}")
            self.logger.warning(f"Commande bloquée: {command} - {security_reason}")
            return None

        # Demander confirmation si nécessaire
        if security_level == 'high' or risk_level == 'high':
            if not self.terminal._confirm_command(command, security_level, security_reason):
                self.console.error("Commande annulée")
                return None

        # Exécuter la commande
        self.console.info("Exécution...")
        self.console.print()

        def stream_output(line: str) -> None:
            self.console.print(f"[output]{line}[/output]")

        result = self.executor.execute_streaming(
            command,
            output_callback=stream_output,
            strict_mode=False
        )

        # Enregistrer dans l'historique
        self.result_handler.handle_result(
            result,
            command,
            user_input,
            "auto",
            skip_output=True
        )

        self.security.record_command_execution(
            command=command,
            success=result['success'],
            risk_level=security_level
        )

        self.parser.add_to_history(user_input, command, result.get('output', ''))

        return result
