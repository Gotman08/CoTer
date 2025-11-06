"""Parser pour convertir les demandes en langage naturel en commandes shell"""

import re
from typing import Dict, Optional, List

from src.utils.command_helpers import SafeLogger
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

    def parse_user_request(self, user_input: str) -> Dict[str, any]:
        """
        Parse la demande utilisateur et retourne une commande shell

        Args:
            user_input: La demande de l'utilisateur en langage naturel

        Returns:
            Dict avec 'command', 'explanation', 'risk_level'
        """
        # Vérifier si c'est une commande spéciale
        if user_input.startswith('/'):
            return self._handle_special_command(user_input)

        # Utiliser l'IA pour parser la demande
        system_prompt = self._get_parsing_system_prompt()

        prompt = f"""Demande utilisateur: "{user_input}"

Génère UNIQUEMENT la commande shell Linux correspondante. Ne fournis AUCUNE explication, juste la commande.
Si la commande est dangereuse ou destructive, commence ta réponse par [DANGER].
Si aucune commande shell n'est appropriée, réponds SEULEMENT par [NO_COMMAND] suivi d'une brève explication.

Exemples:
Demande: "liste les fichiers"
Réponse: ls -la

Demande: "montre l'espace disque"
Réponse: df -h

Demande: "supprime tous les fichiers"
Réponse: [DANGER] rm -rf *

Maintenant, analyse cette demande et réponds:"""

        try:
            response = self.ollama_client.generate(prompt, system_prompt=system_prompt)
            return self._process_ai_response(response, user_input)

        except Exception as e:
            self.logger.error(f"Erreur lors du parsing: {e}")
            return {
                'command': None,
                'explanation': f"Erreur lors de l'analyse de votre demande: {e}",
                'risk_level': 'unknown'
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
        Traite la réponse de l'IA

        Args:
            response: Réponse brute de l'IA
            original_request: Demande originale de l'utilisateur

        Returns:
            Dict structuré avec les informations de commande
        """
        response = response.strip()

        # Vérifier si c'est une commande dangereuse
        if response.startswith('[DANGER]'):
            command = response.replace('[DANGER]', '').strip()
            return {
                'command': command,
                'explanation': f"⚠️  Commande dangereuse détectée",
                'risk_level': 'high',
                'original_request': original_request
            }

        # Vérifier si aucune commande n'est appropriée
        if response.startswith('[NO_COMMAND]'):
            explanation = response.replace('[NO_COMMAND]', '').strip()
            return {
                'command': None,
                'explanation': explanation or "Je ne peux pas convertir cela en commande shell.",
                'risk_level': 'none',
                'original_request': original_request
            }

        # Nettoyer la réponse (enlever markdown, etc.)
        command = self._clean_command(response)

        # Déterminer le niveau de risque avec le RiskAssessor centralisé
        assessment = self.risk_assessor.assess_risk(command)

        return {
            'command': command,
            'explanation': f"Commande générée: {command}",
            'risk_level': assessment.level.value,
            'original_request': original_request
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
