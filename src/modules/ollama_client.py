"""Client pour interagir avec Ollama"""

import requests
import json
from typing import Dict, Optional, Generator

class OllamaClient:
    """Client pour l'API Ollama"""

    # Limites de buffer pour éviter surcharge mémoire (CSAPP Ch.10)
    MAX_CONVERSATION_HISTORY = 50  # Messages max dans l'historique
    MAX_RESPONSE_SIZE_BYTES = 1 * 1024 * 1024  # 1MB max pour une réponse
    MAX_STREAM_CHUNK_SIZE = 8192  # 8KB par chunk en streaming

    def __init__(self, host: str, model: str, timeout: int = 120, logger=None, cache_manager=None,
                 max_history: Optional[int] = None):
        """
        Initialise le client Ollama

        Args:
            host: URL de l'hôte Ollama (ex: http://localhost:11434)
            model: Nom du modèle à utiliser (ex: llama2)
            timeout: Timeout en secondes pour les requêtes
            logger: Logger pour les messages
            cache_manager: Gestionnaire de cache optionnel (CacheManager)
            max_history: Taille max de l'historique (None = utiliser MAX_CONVERSATION_HISTORY)
        """
        self.host = host.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.logger = logger
        self.cache_manager = cache_manager
        self.conversation_history = []
        self.max_history = max_history or self.MAX_CONVERSATION_HISTORY

        if self.cache_manager and self.logger:
            self.logger.info("Cache Ollama activé")

        if self.logger:
            self.logger.debug(f"Buffer limits: max_history={self.max_history}, "
                            f"max_response={self.MAX_RESPONSE_SIZE_BYTES / 1024:.0f}KB")

    def generate(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False) -> str:
        """
        Génère une réponse à partir d'un prompt

        Args:
            prompt: Le prompt utilisateur
            system_prompt: Instructions système optionnelles
            stream: Si True, retourne un générateur pour le streaming

        Returns:
            La réponse générée par le modèle
        """
        # Vérifier le cache d'abord (pas pour le streaming)
        if not stream and self.cache_manager:
            cached_response = self.cache_manager.get(prompt, self.model, system_prompt)
            if cached_response:
                if self.logger:
                    self.logger.debug("✅ Réponse trouvée dans le cache")
                return cached_response

        url = f"{self.host}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            if self.logger:
                self.logger.debug(f"Envoi du prompt à Ollama: {prompt[:100]}...")

            response = requests.post(url, json=payload, timeout=self.timeout, stream=stream)
            response.raise_for_status()

            if stream:
                return self._handle_stream(response)
            else:
                result = response.json()
                generated_response = result.get('response', '')

                # Vérifier la taille de la réponse (protection mémoire)
                response_size = len(generated_response.encode('utf-8'))
                if response_size > self.MAX_RESPONSE_SIZE_BYTES:
                    if self.logger:
                        self.logger.warning(f"Réponse tronquée: {response_size / 1024:.1f}KB "
                                          f"> {self.MAX_RESPONSE_SIZE_BYTES / 1024:.0f}KB")
                    # Tronquer à la limite
                    generated_response = generated_response[:self.MAX_RESPONSE_SIZE_BYTES]
                    generated_response += "\n\n[... Réponse tronquée pour limiter l'utilisation mémoire ...]"

                # Stocker dans le cache
                if self.cache_manager and generated_response:
                    self.cache_manager.set(prompt, generated_response, self.model, system_prompt)

                return generated_response

        except requests.exceptions.Timeout:
            error_msg = f"Timeout lors de la requête à Ollama (>{self.timeout}s)"
            if self.logger:
                self.logger.error(error_msg)
            return f"Erreur: {error_msg}"

        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur de connexion à Ollama: {e}"
            if self.logger:
                self.logger.error(error_msg)
            return f"Erreur: {error_msg}"

    def _handle_stream(self, response) -> Generator[str, None, None]:
        """Gère le streaming de la réponse avec limite de buffer (CSAPP Ch.10)"""
        total_bytes = 0

        for line in response.iter_lines(chunk_size=self.MAX_STREAM_CHUNK_SIZE):
            if line:
                try:
                    data = json.loads(line)
                    if 'response' in data:
                        chunk = data['response']
                        chunk_size = len(chunk.encode('utf-8'))

                        # Vérifier la limite totale
                        if total_bytes + chunk_size > self.MAX_RESPONSE_SIZE_BYTES:
                            remaining = self.MAX_RESPONSE_SIZE_BYTES - total_bytes
                            if remaining > 0:
                                yield chunk[:remaining]
                            if self.logger:
                                self.logger.warning(f"Stream tronqué à {self.MAX_RESPONSE_SIZE_BYTES / 1024:.0f}KB")
                            yield "\n\n[... Stream tronqué pour limiter l'utilisation mémoire ...]"
                            break

                        total_bytes += chunk_size
                        yield chunk
                except json.JSONDecodeError:
                    continue

    def _trim_history(self):
        """Limite la taille de l'historique pour éviter surcharge mémoire (CSAPP Ch.10)"""
        if len(self.conversation_history) > self.max_history:
            # Garder seulement les N derniers messages
            removed_count = len(self.conversation_history) - self.max_history
            self.conversation_history = self.conversation_history[-self.max_history:]

            if self.logger:
                self.logger.debug(f"Historique tronqué: {removed_count} messages supprimés "
                                f"(limite: {self.max_history})")

    def chat(self, message: str, system_prompt: Optional[str] = None) -> str:
        """
        Envoie un message dans une conversation avec gestion limitée de l'historique

        Args:
            message: Le message utilisateur
            system_prompt: Instructions système optionnelles

        Returns:
            La réponse du modèle
        """
        url = f"{self.host}/api/chat"

        # Ajouter le message à l'historique
        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        # Limiter la taille de l'historique (protection mémoire)
        self._trim_history()

        payload = {
            "model": self.model,
            "messages": self.conversation_history,
            "stream": False
        }

        if system_prompt:
            payload["messages"].insert(0, {
                "role": "system",
                "content": system_prompt
            })

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()
            assistant_message = result.get('message', {}).get('content', '')

            # Ajouter la réponse à l'historique
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur lors du chat avec Ollama: {e}"
            if self.logger:
                self.logger.error(error_msg)
            return f"Erreur: {error_msg}"

    def clear_history(self):
        """Efface l'historique de conversation"""
        self.conversation_history = []
        if self.logger:
            self.logger.info("Historique de conversation effacé")

    def check_connection(self) -> bool:
        """
        Vérifie la connexion à Ollama

        Returns:
            True si la connexion est établie, False sinon
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()
            if self.logger:
                self.logger.info("Connexion à Ollama établie")
            return True
        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.error(f"Impossible de se connecter à Ollama: {e}")
            return False

    def list_models(self) -> list:
        """
        Liste les modèles disponibles

        Returns:
            Liste des modèles disponibles
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.error(f"Erreur lors de la récupération des modèles: {e}")
            return []

    def get_cache_stats(self) -> Dict:
        """
        Retourne les statistiques du cache

        Returns:
            Dict avec les stats du cache ou None si pas de cache
        """
        if self.cache_manager:
            return self.cache_manager.get_stats()
        return {'enabled': False}

    def clear_cache(self):
        """Efface le cache Ollama"""
        if self.cache_manager:
            self.cache_manager.clear()
            if self.logger:
                self.logger.info("Cache Ollama effacé")
        else:
            if self.logger:
                self.logger.warning("Pas de cache à effacer")
