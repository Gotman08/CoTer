"""
Processeur de streaming IA avec affichage des balises en temps réel
Centralise la logique de streaming pour éviter la duplication de code
"""

from typing import Dict, Any, Iterator, Optional, List
import logging
from src.utils.tag_parser import TagParser
from src.terminal.tag_display import TagDisplay
from src.core.exceptions import StreamingError

logger = logging.getLogger(__name__)


class AIStreamProcessor:
    """
    Processeur de streaming pour les réponses IA

    Responsabilités:
    - Consommer le stream token par token
    - Détecter et afficher les balises en temps réel
    - Gérer les erreurs et fallbacks
    - Retourner le résultat parsé final

    AVANTAGES:
    - Élimine la duplication entre _stream_ai_response_with_tags et _stream_ai_response_with_history
    - Centralise la logique de streaming
    - Simplifie les tests
    - Respecte le Single Responsibility Principle
    """

    def __init__(self, console, tag_parser: TagParser, tag_display: TagDisplay, parser):
        """
        Initialise le processeur de streaming

        Args:
            console: Console Rich pour l'affichage
            tag_parser: Parser de balises
            tag_display: Afficheur de balises
            parser: CommandParser pour le traitement final
        """
        self.console = console
        self.tag_parser = tag_parser
        self.tag_display = tag_display
        self.parser = parser

    def process_stream(
        self,
        stream_generator: Iterator[str],
        user_input: str,
        context_label: str = "STREAMING"
    ) -> Dict[str, Any]:
        """
        Traite un stream IA token par token avec affichage des balises

        Args:
            stream_generator: Générateur de tokens IA
            user_input: Demande utilisateur originale
            context_label: Label pour les logs (ex: "STREAMING", "STREAMING WITH HISTORY")

        Returns:
            Dict avec command, explanation, risk_level, parsed_sections

        Raises:
            StreamingError: Si le streaming échoue et qu'aucune donnée n'est récupérable
        """
        self.console.print()  # Ligne vide avant
        logger.info(f"[{context_label} START] Parsing request: {user_input[:100]}...")

        # Variables pour tracking des balises
        accumulated_text = ""
        current_tag = None
        tag_content = ""
        in_tag = False
        token_count = 0

        try:
            # Consommer le stream token par token
            for token in stream_generator:
                token_count += 1
                logger.debug(f"[TOKEN #{token_count}] Received: {repr(token[:30])}")
                accumulated_text += token

                # Détecter les balises au fur et à mesure
                if '[' in token:
                    in_tag = True

                if in_tag and ']' in token:
                    # Une balise vient d'être complétée, l'extraire
                    tag_match = accumulated_text.rfind('[')
                    if tag_match != -1:
                        tag_end = accumulated_text.find(']', tag_match)
                        if tag_end != -1:
                            potential_tag = accumulated_text[tag_match+1:tag_end]

                            # Si c'est une balise connue, afficher la section précédente
                            if self.tag_parser.is_known_tag(potential_tag):
                                if current_tag and tag_content.strip():
                                    self.tag_display.display_tag(current_tag, tag_content.strip())

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
            logger.info(f"[{context_label} END] Received {token_count} tokens, {len(accumulated_text)} chars total")

            # Récupérer le résultat final du générateur
            result = self._extract_generator_result(stream_generator)

            # Si pas de résultat, parser manuellement le texte accumulé
            if result is None:
                result = self.parser._process_ai_response(accumulated_text, user_input)

            return result

        except Exception as e:
            # Logger l'erreur complète avec traceback
            logger.error(f"Erreur lors du streaming: {e}", exc_info=True)

            # Afficher l'erreur en console de manière visible
            self.console.print()
            self.console.error(f"Erreur lors du streaming IA: {str(e)}")

            # Logging détaillé en mode debug
            import traceback
            traceback_str = traceback.format_exc()
            logger.debug(f"Traceback complet:\n{traceback_str}")

            # Fallback: parser le texte accumulé si on a reçu quelque chose
            if accumulated_text:
                logger.info(f"Fallback: parsing {len(accumulated_text)} chars accumulated before error")
                self.console.warning("Tentative de récupération partielle...")
                return self.parser._process_ai_response(accumulated_text, user_input)

            # Aucune donnée récupérable - lever une exception typée
            self.console.error("Aucune donnée récupérable. Vérifiez que le serveur Ollama est actif.")
            raise StreamingError(
                message=f"Le streaming a échoué sans données récupérables: {e}",
                partial_data=None
            )

    def _extract_generator_result(self, stream_generator: Iterator[str]) -> Optional[Dict[str, Any]]:
        """
        Extrait la valeur de retour d'un générateur Python

        Args:
            stream_generator: Générateur dont on veut la valeur de retour

        Returns:
            Valeur de retour du générateur (via StopIteration.value) ou None
        """
        try:
            # Consommer tout le générateur jusqu'à StopIteration
            while True:
                next(stream_generator)
        except StopIteration as e:
            # La valeur de retour du générateur est dans e.value
            return e.value if hasattr(e, 'value') else None
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction du résultat: {e}")
            return None
