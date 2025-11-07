"""Parser pour convertir les demandes en langage naturel en commandes shell"""

import re
from typing import Dict, Optional, List

from src.utils.command_helpers import SafeLogger
from src.utils.tag_parser import TagParser
from src.security import RiskAssessor

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
            # Mode streaming: retourner un générateur
            return self._stream_parse(prompt, system_prompt, user_input)

        except Exception as e:
            self.logger.error(f"Erreur lors du streaming: {e}")
            yield from []
            return {
                'command': None,
                'explanation': f"Erreur lors du streaming: {e}",
                'risk_level': 'unknown',
                'parsed_sections': {}
            }

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
        return """Tu es un assistant spécialisé dans la conversion de demandes en langage naturel vers des commandes shell Linux.
Tu dois UNIQUEMENT retourner la commande shell, sans explication ni formatage markdown.
Tu connais parfaitement bash, les commandes Linux standards et les outils système.
Privilégie les commandes sûres et simples.
Pour les opérations dangereuses (suppression, modification système), préfixe par [DANGER].
Si la demande n'est pas une action système, préfixe par [NO_COMMAND]."""

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
