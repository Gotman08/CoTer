"""
Handler pour les commandes spéciales (commençant par /)

Extrait de terminal_interface.py pour réduire la complexité
et appliquer le principe SRP (Single Responsibility Principle).
"""

from typing import TYPE_CHECKING, Optional
from config import prompts

if TYPE_CHECKING:
    from src.terminal_interface import TerminalInterface


class SpecialCommandHandler:
    """
    Gère l'exécution des commandes spéciales du terminal.

    Les commandes spéciales sont celles qui commencent par '/' et permettent
    de contrôler le comportement du terminal (changement de mode, aide, etc.).

    Attributes:
        terminal: Référence vers l'instance TerminalInterface parente
    """

    def __init__(self, terminal: 'TerminalInterface'):
        """
        Initialise le gestionnaire de commandes spéciales.

        Args:
            terminal: Instance de TerminalInterface pour accéder aux composants
        """
        self.terminal = terminal
        self.console = terminal.console
        self.logger = terminal.logger

    def handle_command(self, command: str) -> bool:
        """
        Traite une commande spéciale.

        Args:
            command: Commande spéciale (commence par /)

        Returns:
            True si la commande a été traitée, False sinon
        """
        cmd_lower = command.lower()

        # Commandes de base
        if cmd_lower in ['/quit', '/exit']:
            self._handle_quit()
            return True

        if cmd_lower == '/help':
            self._handle_help()
            return True

        if cmd_lower == '/clear':
            self._handle_clear_history()
            return True

        # Commandes de mode
        if cmd_lower == '/manual':
            self._handle_manual_mode()
            return True

        if cmd_lower == '/auto':
            self._handle_auto_mode()
            return True

        if cmd_lower == '/fast':
            self._handle_fast_mode()
            return True

        if cmd_lower == '/status':
            self._handle_status()
            return True

        # Commandes d'information
        if cmd_lower == '/history':
            self._handle_history()
            return True

        if cmd_lower in ['/models', '/change']:
            self._handle_models()
            return True

        if cmd_lower == '/info':
            self._handle_info()
            return True

        if cmd_lower == '/templates':
            self._handle_templates()
            return True

        if cmd_lower == '/hardware':
            self._handle_hardware()
            return True

        # Commandes agent
        if cmd_lower.startswith('/agent'):
            self._handle_agent_command(command)
            return True

        if cmd_lower == '/pause':
            self._handle_pause()
            return True

        if cmd_lower == '/resume':
            self._handle_resume()
            return True

        if cmd_lower == '/stop':
            self._handle_stop()
            return True

        # Commandes cache
        if cmd_lower.startswith('/cache'):
            self._handle_cache_command(command)
            return True

        # Commandes rollback
        if cmd_lower.startswith('/rollback'):
            self._handle_rollback_command(command)
            return True

        # Commandes sécurité
        if cmd_lower == '/security':
            self._handle_security()
            return True

        # Commandes corrections
        if cmd_lower.startswith('/corrections'):
            self._handle_corrections_command(command)
            return True

        # Commandes plan
        if cmd_lower.startswith('/plan'):
            self._handle_plan_command(command)
            return True

        # Commande inconnue
        self.console.print()
        self.console.error(f"Commande inconnue: {command}")
        self.console.print("[dim]Tapez /help pour voir les commandes disponibles[/dim]")
        return False

    # ═══════════════════════════════════════════════════════════════
    # COMMANDES DE BASE
    # ═══════════════════════════════════════════════════════════════

    def _handle_quit(self):
        """Quitte l'application"""
        self.terminal._quit()

    def _handle_help(self):
        """Affiche l'aide"""
        self.console.print_help(prompts.HELP_TEXT)

    def _handle_clear_history(self):
        """Efface l'historique"""
        self.logger.info("Effacement de l'historique demandé")
        self.terminal.parser.clear_history()
        self.terminal.ollama.clear_history()
        self.console.print()
        self.console.success("Historique effacé")

    # ═══════════════════════════════════════════════════════════════
    # COMMANDES DE MODE
    # ═══════════════════════════════════════════════════════════════

    def _handle_manual_mode(self):
        """Bascule en mode MANUAL"""
        if self.terminal.shell_engine.switch_to_manual():
            self.logger.info("Changement de mode: → MANUAL")
            self.console.print()
            self.console.success("Mode MANUAL activé")
            self.console.print(f"[dim]{self.terminal.shell_engine.get_mode_description()}[/dim]")
        else:
            self.console.print()
            self.console.info("Déjà en mode MANUAL")

    def _handle_auto_mode(self):
        """Bascule en mode AUTO"""
        if self.terminal.shell_engine.switch_to_auto():
            self.logger.info("Changement de mode: → AUTO (itératif)")
            self.console.print()
            self.console.success("Mode AUTO activé")
            self.console.print(f"[dim]{self.terminal.shell_engine.get_mode_description()}[/dim]")
        else:
            self.console.print()
            self.console.info("Déjà en mode AUTO")

    def _handle_fast_mode(self):
        """Bascule en mode FAST"""
        if self.terminal.shell_engine.switch_to_fast():
            self.logger.info("Changement de mode: → FAST (one-shot)")
            self.console.print()
            self.console.success("Mode FAST activé")
            self.console.print(f"[dim]{self.terminal.shell_engine.get_mode_description()}[/dim]")
        else:
            self.console.print()
            self.console.info("Déjà en mode FAST")

    def _handle_status(self):
        """Affiche le statut du shell"""
        self.terminal.display_manager.show_shell_status()

    # ═══════════════════════════════════════════════════════════════
    # COMMANDES D'INFORMATION
    # ═══════════════════════════════════════════════════════════════

    def _handle_history(self):
        """Affiche l'historique"""
        self.terminal.display_manager.show_history()

    def _handle_models(self):
        """Liste les modèles disponibles"""
        self.terminal.display_manager.list_models()

    def _handle_info(self):
        """Affiche les informations système"""
        self.terminal.display_manager.show_system_info()

    def _handle_templates(self):
        """Liste les templates disponibles"""
        self.terminal.display_manager.list_templates()

    def _handle_hardware(self):
        """Affiche les informations hardware"""
        self.terminal.display_manager.show_hardware_info()

    # ═══════════════════════════════════════════════════════════════
    # COMMANDES AGENT
    # ═══════════════════════════════════════════════════════════════

    def _handle_agent_command(self, command: str):
        """Gère les commandes /agent"""
        if not self.terminal.agent:
            self.console.print()
            self.console.error("Mode agent autonome désactivé")
            return

        # Basculer en mode AGENT
        self.terminal.shell_engine.switch_to_agent()

        # Extraire la demande après /agent
        request = command[6:].strip()
        if request:
            self.terminal._handle_autonomous_mode(request)
        else:
            self.console.print()
            self.console.info("Usage: /agent <votre demande>")
            self.console.print("[dim]Exemple: /agent crée-moi une API FastAPI[/dim]")

    def _handle_pause(self):
        """Met en pause l'agent"""
        if self.terminal.agent and self.terminal.agent.is_running:
            self.terminal.agent.pause()
            self.console.print()
            self.console.print(prompts.AGENT_PAUSED)
        else:
            self.console.print()
            self.console.error("Aucun agent en cours d'exécution")

    def _handle_resume(self):
        """Reprend l'agent"""
        if self.terminal.agent and self.terminal.agent.is_paused:
            self.terminal.agent.resume()
            self.console.print()
            self.console.success("Agent repris")
        else:
            self.console.print()
            self.console.error("Aucun agent en pause")

    def _handle_stop(self):
        """Arrête l'agent"""
        if self.terminal.agent and self.terminal.agent.is_running:
            self.terminal.agent.stop()
            self.console.print()
            self.console.print(prompts.AGENT_STOPPED)
        else:
            self.console.print()
            self.console.error("Aucun agent en cours d'exécution")

    # ═══════════════════════════════════════════════════════════════
    # COMMANDES CACHE
    # ═══════════════════════════════════════════════════════════════

    def _handle_cache_command(self, command: str):
        """Gère les commandes /cache"""
        parts = command.split()
        if len(parts) == 1:
            # /cache seul = afficher stats
            self.terminal.display_manager.show_cache_stats()
        elif parts[1].lower() == 'stats':
            self.terminal.display_manager.show_cache_stats()
        elif parts[1].lower() == 'clear':
            self.terminal.display_manager.clear_cache()
        else:
            self.console.print()
            self.console.error("Commande cache inconnue")
            self.console.print("[dim]Usage: /cache [stats|clear][/dim]")

    # ═══════════════════════════════════════════════════════════════
    # COMMANDES ROLLBACK
    # ═══════════════════════════════════════════════════════════════

    def _handle_rollback_command(self, command: str):
        """Gère les commandes /rollback"""
        if not self.terminal.agent:
            self.console.print()
            self.console.error("Le mode agent n'est pas activé")
            return

        parts = command.split()
        if len(parts) == 1:
            # /rollback seul = afficher snapshots disponibles
            self.terminal.display_manager.show_snapshots()
        elif parts[1].lower() == 'list':
            self.terminal.display_manager.show_snapshots()
        elif parts[1].lower() == 'restore':
            # /rollback restore [snapshot_id]
            snapshot_id = parts[2] if len(parts) > 2 else None
            self.terminal.display_manager.restore_snapshot(snapshot_id)
        elif parts[1].lower() == 'stats':
            self.terminal.display_manager.show_rollback_stats()
        else:
            self.console.print()
            self.console.error("Commande rollback inconnue")
            self.console.print("[dim]Usage: /rollback [list|restore|stats][/dim]")

    # ═══════════════════════════════════════════════════════════════
    # COMMANDES SÉCURITÉ & CORRECTIONS
    # ═══════════════════════════════════════════════════════════════

    def _handle_security(self):
        """Affiche le rapport de sécurité"""
        self.terminal.display_manager.show_security_report()

    def _handle_corrections_command(self, command: str):
        """Gère les commandes /corrections"""
        if not self.terminal.agent:
            self.console.print()
            self.console.error("Le mode agent n'est pas activé")
            return

        parts = command.split()
        if len(parts) == 1 or parts[1].lower() == 'stats':
            self.terminal.display_manager.show_correction_stats()
        elif parts[1].lower() == 'last':
            self.terminal.display_manager.show_last_error()
        else:
            self.console.print()
            self.console.error("Commande corrections inconnue")
            self.console.print("[dim]Usage: /corrections [stats|last][/dim]")

    # ═══════════════════════════════════════════════════════════════
    # COMMANDES PLAN
    # ═══════════════════════════════════════════════════════════════

    def _handle_plan_command(self, command: str):
        """Gère les commandes /plan"""
        if not self.terminal.background_planner:
            self.console.print()
            self.console.error("La planification en arrière-plan n'est pas activée")
            return

        parts = command.split()
        if len(parts) == 1:
            self._handle_plan_show()
        elif parts[1].lower() == 'stats':
            self._handle_plan_stats()
        elif parts[1].lower() == 'list':
            self._handle_plan_list()
        elif parts[1].lower() == 'clear':
            self._handle_plan_clear()
        else:
            self.console.print()
            self.console.error("Commande plan inconnue")
            self.console.print("[dim]Usage: /plan [stats|list|clear][/dim]")

    def _handle_plan_show(self):
        """Affiche le dernier plan disponible"""
        latest_plan_data = self.terminal.background_planner.get_plan_from_queue()

        if not latest_plan_data:
            # Vérifier dans le stockage
            if self.terminal.plan_storage:
                stored_plan = self.terminal.plan_storage.get_latest_plan(executed=False)
                if stored_plan:
                    latest_plan_data = {
                        'plan': stored_plan['plan'],
                        'analysis': stored_plan['analysis'],
                        'request_id': stored_plan['request_id']
                    }

        if latest_plan_data:
            self.terminal.display_manager.show_background_plan(latest_plan_data)

            # Proposer d'exécuter
            self.console.print()
            response = input("Exécuter ce plan ? (oui/non): ").strip().lower()
            if response in ['oui', 'o', 'yes', 'y']:
                plan = latest_plan_data['plan']
                exec_result = self.terminal.agent.execute_plan(plan)

                if exec_result.get('success'):
                    self.console.success("✓ Plan exécuté avec succès!")

                    # Marquer comme exécuté
                    if self.terminal.plan_storage:
                        recent_plans = self.terminal.plan_storage.get_recent_plans(limit=1, executed=False)
                        if recent_plans:
                            self.terminal.plan_storage.mark_executed(recent_plans[0]['id'], 'success')
                else:
                    self.console.error("❌ Échec de l'exécution du plan")
                    if self.terminal.plan_storage:
                        recent_plans = self.terminal.plan_storage.get_recent_plans(limit=1, executed=False)
                        if recent_plans:
                            self.terminal.plan_storage.mark_executed(recent_plans[0]['id'], 'failed')
        else:
            self.console.print()
            self.console.warning("Aucun plan disponible")

    def _handle_plan_stats(self):
        """Affiche les statistiques du planificateur"""
        stats = self.terminal.background_planner.get_stats()
        self.terminal.display_manager.show_plan_stats(stats)

        # Ajouter les stats du stockage
        if self.terminal.plan_storage:
            storage_stats = self.terminal.plan_storage.get_stats()
            self.console.print()
            self.console.print("[subtitle]Stockage des plans:[/subtitle]")
            self.console.print(f"   [label]Total:[/label] {storage_stats['total_plans']}")
            self.console.print(f"   [label]Exécutés:[/label] {storage_stats['executed']}")
            self.console.print(f"   [label]En attente:[/label] {storage_stats['pending']}")

    def _handle_plan_list(self):
        """Liste les plans récents"""
        if not self.terminal.plan_storage:
            self.console.print()
            self.console.error("Stockage des plans non disponible")
            return

        recent_plans = self.terminal.plan_storage.get_recent_plans(limit=10)

        if not recent_plans:
            self.console.print()
            self.console.warning("Aucun plan dans l'historique")
        else:
            self.console.print()
            self.console.print("[title]PLANS RÉCENTS[/title]")
            self.console.print()

            for idx, plan_data in enumerate(recent_plans, 1):
                status_icon = "✓" if plan_data['executed'] else "⏸"
                status_text = "Exécuté" if plan_data['executed'] else "En attente"

                self.console.print(f"[label]{idx}.[/label] {status_icon} {plan_data['user_request'][:60]}")
                self.console.print(f"   [dim]Type:[/dim] {plan_data['analysis'].get('project_type', 'N/A')}")
                self.console.print(f"   [dim]Date:[/dim] {plan_data['created_at']}")
                self.console.print(f"   [dim]Statut:[/dim] {status_text}")
                self.console.print()

    def _handle_plan_clear(self):
        """Efface les résultats en attente"""
        self.terminal.background_planner.clear_results()
        self.console.print()
        self.console.success("Plans en attente effacés")
