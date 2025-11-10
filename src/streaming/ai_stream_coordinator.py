"""
Coordinateur pour le streaming des réponses IA

Ce module unifie la logique de streaming pour éliminer la duplication
entre _stream_ai_response_with_tags et _stream_ai_response_with_history.
"""

from typing import Generator, Optional, Dict, Any


class AIStreamCoordinator:
    """
    Coordonne le streaming des réponses IA avec affichage en temps réel.

    Cette classe centralise la logique de streaming qui était dupliquée
    dans terminal_interface.py, appliquant le principe DRY.

    Attributes:
        parser: Instance de CommandParser pour générer les streams
        stream_processor: Instance d'AIStreamProcessor pour afficher le stream
        logger: Logger pour les messages de debug
    """

    def __init__(self, parser, stream_processor, logger=None):
        """
        Initialise le coordinateur de streaming.

        Args:
            parser: CommandParser pour générer les requêtes IA
            stream_processor: AIStreamProcessor pour afficher le stream
            logger: Logger optionnel pour les messages
        """
        self.parser = parser
        self.stream_processor = stream_processor
        self.logger = logger

    def stream_ai_response(
        self,
        user_input: str,
        context_history: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Stream une réponse IA avec ou sans historique de contexte.

        Cette méthode unifie _stream_ai_response_with_tags et
        _stream_ai_response_with_history en une seule fonction.

        Args:
            user_input: Demande utilisateur
            context_history: Historique optionnel des étapes précédentes
                           (None pour première requête, list pour itérations suivantes)

        Returns:
            Dict avec command, explanation, risk_level, parsed_sections
        """
        # Déterminer le type de streaming
        if context_history:
            # Avec historique (mode itératif)
            if self.logger:
                self.logger.info(
                    f"[STREAMING WITH HISTORY] Step avec {len(context_history)} étapes précédentes"
                )
            stream_generator = self.parser.parse_with_history(user_input, context_history)
            context_label = "STREAMING WITH HISTORY"
        else:
            # Sans historique (première requête)
            if self.logger:
                self.logger.debug("[STREAMING] Première requête sans historique")
            stream_generator = self.parser.parse_user_request_stream(user_input)
            context_label = "STREAMING"

        # Déléguer au processeur de streaming
        return self.stream_processor.process_stream(
            stream_generator,
            user_input,
            context_label=context_label
        )

    def stream_fast_mode_response(self, user_input: str) -> Dict[str, Any]:
        """
        Stream une réponse IA en mode FAST avec prompt système spécifique.

        Args:
            user_input: Demande utilisateur

        Returns:
            Dict avec command, explanation, risk_level, parsed_sections
        """
        from config.prompts import SYSTEM_PROMPT_FAST

        # Sauvegarder le prompt original
        original_prompt_method = self.parser._get_parsing_system_prompt

        # Override temporaire pour utiliser SYSTEM_PROMPT_FAST
        self.parser._get_parsing_system_prompt = lambda: SYSTEM_PROMPT_FAST

        try:
            # Utiliser la méthode unifiée
            return self.stream_ai_response(user_input, context_history=None)
        finally:
            # Restaurer le prompt original
            self.parser._get_parsing_system_prompt = original_prompt_method
