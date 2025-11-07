"""
Gestionnaire de configuration utilisateur persistante.
Permet de sauvegarder les préférences de l'utilisateur entre les sessions.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import platform

logger = logging.getLogger(__name__)


class UserConfigManager:
    r"""
    Gère la configuration utilisateur persistante dans un fichier JSON.

    Emplacement du fichier de configuration :
    - Linux/Mac: ~/.config/coter/config.json
    - Windows: %USERPROFILE%\.coter\config.json
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialise le gestionnaire de configuration utilisateur.

        Args:
            config_path: Chemin personnalisé pour le fichier de config (optionnel)
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = self._get_default_config_path()

        self.config_dir = self.config_path.parent
        self._ensure_config_dir()

        # Configuration par défaut
        self.default_config = {
            'last_model': None,
            'model_history': [],
            'preferences': {
                'auto_warmup': True
            }
        }

        # Charger la configuration existante
        self.config = self.load_config()

    def _get_default_config_path(self) -> Path:
        """
        Détermine le chemin par défaut du fichier de configuration
        selon le système d'exploitation.

        Returns:
            Path: Chemin vers le fichier de configuration
        """
        system = platform.system()

        if system == "Windows":
            # Windows: %USERPROFILE%\.coter\config.json
            user_home = Path.home()
            config_dir = user_home / ".coter"
        else:
            # Linux/Mac: ~/.config/coter/config.json
            user_home = Path.home()
            config_dir = user_home / ".config" / "coter"

        return config_dir / "config.json"

    def _ensure_config_dir(self):
        """Crée le répertoire de configuration s'il n'existe pas."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Répertoire de configuration: {self.config_dir}")
        except Exception as e:
            logger.warning(f"Impossible de créer le répertoire de configuration: {e}")

    def load_config(self) -> Dict[str, Any]:
        """
        Charge la configuration utilisateur depuis le fichier JSON.

        Returns:
            Dict: Configuration chargée ou configuration par défaut
        """
        if not self.config_path.exists():
            logger.debug(f"Aucune configuration utilisateur trouvée à {self.config_path}")
            return self.default_config.copy()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Fusionner avec les valeurs par défaut pour les clés manquantes
            merged_config = self.default_config.copy()
            merged_config.update(config)

            logger.info(f"Configuration utilisateur chargée depuis {self.config_path}")
            return merged_config

        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON dans {self.config_path}: {e}")
            return self.default_config.copy()

        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            return self.default_config.copy()

    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """
        Sauvegarde la configuration utilisateur dans le fichier JSON.

        Args:
            config: Configuration à sauvegarder (utilise self.config si None)
        """
        if config is None:
            config = self.config

        try:
            self._ensure_config_dir()

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.debug(f"Configuration sauvegardée dans {self.config_path}")

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")

    def get_last_model(self) -> Optional[str]:
        """
        Récupère le dernier modèle LLM utilisé.

        Returns:
            str | None: Nom du dernier modèle ou None si aucun
        """
        return self.config.get('last_model')

    def save_last_model(self, model_name: str):
        """
        Sauvegarde le modèle LLM sélectionné et l'ajoute à l'historique.

        Args:
            model_name: Nom du modèle à sauvegarder
        """
        # Mettre à jour le dernier modèle
        self.config['last_model'] = model_name

        # Ajouter à l'historique (sans doublons)
        model_history = self.config.get('model_history', [])
        if model_name not in model_history:
            model_history.append(model_name)

        # Limiter l'historique à 10 modèles
        if len(model_history) > 10:
            model_history = model_history[-10:]

        self.config['model_history'] = model_history

        # Sauvegarder
        self.save_config()
        logger.info(f"Modèle sauvegardé: {model_name}")

    def get_model_history(self) -> list:
        """
        Récupère l'historique des modèles utilisés.

        Returns:
            list: Liste des noms de modèles dans l'ordre d'utilisation
        """
        return self.config.get('model_history', [])

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Récupère une préférence utilisateur.

        Args:
            key: Clé de la préférence
            default: Valeur par défaut si la clé n'existe pas

        Returns:
            Valeur de la préférence ou valeur par défaut
        """
        return self.config.get('preferences', {}).get(key, default)

    def set_preference(self, key: str, value: Any):
        """
        Définit une préférence utilisateur.

        Args:
            key: Clé de la préférence
            value: Valeur à sauvegarder
        """
        if 'preferences' not in self.config:
            self.config['preferences'] = {}

        self.config['preferences'][key] = value
        self.save_config()
        logger.debug(f"Préférence '{key}' définie à: {value}")

    def clear_config(self):
        """Réinitialise la configuration aux valeurs par défaut."""
        self.config = self.default_config.copy()
        self.save_config()
        logger.info("Configuration réinitialisée aux valeurs par défaut")

    def get_config_path(self) -> Path:
        """
        Retourne le chemin du fichier de configuration.

        Returns:
            Path: Chemin absolu du fichier de configuration
        """
        return self.config_path
