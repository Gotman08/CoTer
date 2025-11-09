"""Parser pour convertir les demandes en langage naturel en commandes shell"""

import re
from typing import Dict, Optional, List

from src.utils.command_helpers import SafeLogger
from src.utils.tag_parser import TagParser
from src.security import RiskAssessor
from config.prompts import SYSTEM_PROMPT_MAIN

class CommandParser:
    """Parse les demandes utilisateur et génère des commandes shell appropriées"""

    def __init__(self, ollama_client, logger=None):
        """
        Initialise le parser de commandes

        Args:
            ollama_client: Client Ollama pour l'analyse intelligente
            logger: Logger pour les messages
        """
        self.ollama_client = ollama_client
        self.logger = SafeLogger(logger)
        self.risk_assessor = RiskAssessor()
        self.command_history = []
        self.tag_parser = TagParser()

    def parse_user_request(self, user_input: str) -> Dict[str, any]:
        """
        Parse la demande utilisateur et retourne une commande shell (mode non-streaming)

        Args:
            user_input: La demande de l'utilisateur en langage naturel

        Returns:
            Dict avec 'command', 'explanation', 'risk_level', 'parsed_sections'
        """
        # Vérifier si c'est une commande spéciale
        if user_input.startswith('/'):
            return self._handle_special_command(user_input)

        # Utiliser l'IA pour parser la demande
        system_prompt = self._get_parsing_system_prompt()

        # Le prompt est maintenant obsolète car le system_prompt gère déjà les balises
        prompt = f"""Demande utilisateur: "{user_input}"

Analyse cette demande et génère la commande appropriée."""

        try:
            # Mode non-streaming: comportement classique
            response = self.ollama_client.generate(prompt, system_prompt=system_prompt)
            return self._process_ai_response(response, user_input)

        except Exception as e:
            self.logger.error(f"Erreur lors du parsing: {e}")
            return {
                'command': None,
                'explanation': f"Erreur lors de l'analyse de votre demande: {e}",
                'risk_level': 'unknown',
                'parsed_sections': {}
            }

    def parse_user_request_stream(self, user_input: str):
        """
        Parse la demande utilisateur en mode streaming

        Args:
            user_input: La demande de l'utilisateur en langage naturel

        Yields:
            Tokens de la réponse IA

        Returns:
            Dict avec 'command', 'explanation', 'risk_level', 'parsed_sections'
        """
        # Vérifier si c'est une commande spéciale
        if user_input.startswith('/'):
            # Pour les commandes spéciales, pas de streaming
            yield from []
            return self._handle_special_command(user_input)

        # Utiliser l'IA pour parser la demande
        system_prompt = self._get_parsing_system_prompt()

        prompt = f"""Demande utilisateur: "{user_input}"

Analyse cette demande et génère la commande appropriée."""

        try:
            # Mode streaming: yield depuis le générateur au lieu de le retourner
            yield from self._stream_parse(prompt, system_prompt, user_input)

        except Exception as e:
            self.logger.error(f"Erreur lors du streaming: {e}")
            yield from []
            return {
                'command': None,
                'explanation': f"Erreur lors du streaming: {e}",
                'risk_level': 'unknown',
                'parsed_sections': {}
            }

    def parse_with_history(self, user_input: str, context_history: List[Dict]):
        """
        Parse la demande utilisateur en mode streaming AVEC historique (mode itératif)

        Args:
            user_input: La demande de l'utilisateur en langage naturel
            context_history: Historique des commandes et résultats précédents
                Format: [{'command': str, 'output': str, 'success': bool}, ...]

        Yields:
            Tokens de la réponse IA

        Returns:
            Dict avec 'command', 'explanation', 'risk_level', 'parsed_sections'
        """
        self.logger.info(f"Parse avec historique - {len(context_history)} étapes précédentes")

        # Vérifier si c'est une commande spéciale
        if user_input.startswith('/'):
            yield from []
            return self._handle_special_command(user_input)

        # Utiliser l'IA pour parser la demande avec contexte
        system_prompt = self._get_parsing_system_prompt()

        # Formater le contexte de l'historique
        context_text = self._format_history_context(context_history)
        self.logger.debug(f"Contexte formaté: {len(context_text)} caractères")

        # Construire le prompt avec le contexte
        prompt = f"""Demande utilisateur initiale: "{user_input}"

{context_text}

Basé sur l'historique ci-dessus, génère la PROCHAINE commande logique pour continuer la tâche.
Si la tâche est complétée, indique "✓ Tâche terminée" dans la description.
Si tu ne peux pas continuer, indique "✗ Impossible de continuer" dans la description."""

        try:
            # Mode streaming avec contexte
            self.logger.debug("Lancement du streaming avec contexte historique")
            yield from self._stream_parse(prompt, system_prompt, user_input)

        except Exception as e:
            self.logger.error(f"Erreur lors du streaming avec historique: {e}")
            yield from []
            return {
                'command': None,
                'explanation': f"Erreur lors du streaming: {e}",
                'risk_level': 'unknown',
                'parsed_sections': {}
            }

    def _format_history_context(self, context_history: List[Dict]) -> str:
        """
        Formate l'historique des commandes pour le prompt IA

        Args:
            context_history: Liste des étapes précédentes

        Returns:
            String formaté pour inclusion dans le prompt
        """
        if not context_history:
            return "Historique: Aucune commande exécutée encore."

        self.logger.debug(f"Formatage de {len(context_history)} étapes d'historique")

        lines = ["Historique des étapes précédentes:"]
        for i, step in enumerate(context_history, 1):
            command = step.get('command', 'N/A')
            output = step.get('output', '')
            success = step.get('success', False)

            # Limiter la taille de l'output pour ne pas surcharger le prompt
            output_preview = output[:300] + "..." if len(output) > 300 else output

            status = "✓ Succès" if success else "✗ Échec"
            lines.append(f"\nÉtape {i}: {status}")
            lines.append(f"Commande: {command}")
            if output_preview:
                lines.append(f"Résultat: {output_preview}")

        self.logger.debug(f"Historique formaté avec succès ({len(lines)} lignes)")

        return "\n".join(lines)

    def _stream_parse(self, prompt: str, system_prompt: str, user_input: str):
        """
        Parse en mode streaming - yield les tokens au fur et à mesure

        Args:
            prompt: Prompt utilisateur
            system_prompt: Prompt système
            user_input: Input original de l'utilisateur

        Yields:
            Tokens de la réponse IA

        Returns:
            Dict final avec la commande parsée
        """
        # Générer la réponse en streaming
        stream_generator = self.ollama_client.generate(
            prompt,
            system_prompt=system_prompt,
            stream=True
        )

        # Accumuler la réponse complète tout en yieldant les tokens
        full_response = ""
        try:
            for token in stream_generator:
                full_response += token
                yield token

            # Une fois le streaming terminé, parser la réponse complète
            result = self._process_ai_response(full_response, user_input)
            return result

        except Exception as e:
            self.logger.error(f"Erreur lors du streaming: {e}")
            return {
                'command': None,
                'explanation': f"Erreur lors du streaming: {e}",
                'risk_level': 'unknown',
                'parsed_sections': {}
            }

    def _get_parsing_system_prompt(self) -> str:
        """Retourne le prompt système pour le parsing"""
        return SYSTEM_PROMPT_MAIN

    def _process_ai_response(self, response: str, original_request: str) -> Dict[str, any]:
        """
        Traite la réponse de l'IA avec support des balises

        Args:
            response: Réponse brute de l'IA (peut contenir des balises)
            original_request: Demande originale de l'utilisateur

        Returns:
            Dict structuré avec les informations de commande et sections parsées
        """
        response = response.strip()

        # Parser la réponse pour extraire les balises
        parsed_sections = self.tag_parser.parse(response)

        # Vérifier si aucune commande n'est appropriée
        if self.tag_parser.has_tag(parsed_sections, 'no Commande') or \
           self.tag_parser.has_tag(parsed_sections, 'NO_COMMAND'):
            explanation = self.tag_parser.get_tag_content(parsed_sections, 'no Commande') or \
                         self.tag_parser.get_tag_content(parsed_sections, 'NO_COMMAND') or \
                         "Je ne peux pas convertir cela en commande shell."
            return {
                'command': None,
                'explanation': explanation,
                'risk_level': 'none',
                'original_request': original_request,
                'parsed_sections': parsed_sections
            }

        # Extraire la commande (cherche dans [Commande] ou [DANGER])
        command = self.tag_parser.extract_command(parsed_sections)

        # Si aucune commande n'est trouvée dans les balises, fallback sur l'ancienne méthode
        if command is None:
            # Pas de balises utilisées - nettoyer la réponse brute
            command = self._clean_command(response)

        # Vérifier si c'est une commande dangereuse
        is_danger = self.tag_parser.has_tag(parsed_sections, 'DANGER')

        if is_danger:
            return {
                'command': command,
                'explanation': "Commande dangereuse détectée",
                'risk_level': 'high',
                'original_request': original_request,
                'parsed_sections': parsed_sections
            }

        # Déterminer le niveau de risque avec le RiskAssessor centralisé
        assessment = self.risk_assessor.assess_risk(command)

        # Construire l'explication depuis les balises si disponible
        explanation = self.tag_parser.get_tag_content(parsed_sections, 'Description')
        if not explanation:
            explanation = f"Commande générée: {command}"

        return {
            'command': command,
            'explanation': explanation,
            'risk_level': assessment.level.value,
            'original_request': original_request,
            'parsed_sections': parsed_sections
        }

    def _clean_command(self, response: str) -> str:
        """Nettoie la commande de tout formatage superflu"""
        # Enlever les blocs de code markdown
        response = re.sub(r'```(?:bash|shell|sh)?\n?', '', response)
        response = re.sub(r'```\n?', '', response)

        # Enlever les backticks simples
        response = response.replace('`', '')

        # Prendre seulement la première ligne si plusieurs
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if lines:
            return lines[0]

        return response.strip()

    def _handle_special_command(self, command: str) -> Dict[str, any]:
        """Gère les commandes spéciales (commençant par /)"""
        return {
            'command': command,
            'explanation': 'Commande spéciale',
            'risk_level': 'none',
            'is_special': True
        }

    def add_to_history(self, user_input: str, command: str, result: str):
        """Ajoute une commande à l'historique"""
        self.command_history.append({
            'input': user_input,
            'command': command,
            'result': result
        })

    def get_history(self) -> List[Dict]:
        """Retourne l'historique des commandes"""
        return self.command_history

    def clear_history(self):
        """Efface l'historique"""
        self.command_history = []
        if self.logger:
            self.logger.info("Historique des commandes effacé")
