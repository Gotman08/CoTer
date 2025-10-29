#!/usr/bin/env python3
"""
Terminal IA Autonome
Point d'entrée principal de l'application
"""

import sys
import argparse
import multiprocessing
import requests
from typing import List, Tuple, Optional
from simple_term_menu import TerminalMenu
from src.terminal_interface import TerminalInterface
from src.utils.logger import setup_logger
from src.utils import HardwareOptimizer, CacheManager, OllamaManager
from config.settings import Settings
from config import CacheConfig, constants


def check_ollama_connection(host: str, timeout: int = 5) -> bool:
    """
    Vérifie si Ollama est accessible

    Args:
        host: URL du serveur Ollama
        timeout: Timeout en secondes

    Returns:
        True si Ollama est accessible, False sinon
    """
    try:
        response = requests.get(f"{host}/api/tags", timeout=timeout)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False


def get_available_models(host: str, timeout: int = 5) -> List[dict]:
    """
    Récupère la liste des modèles Ollama disponibles avec leurs informations

    Args:
        host: URL du serveur Ollama
        timeout: Timeout en secondes

    Returns:
        Liste de dictionnaires avec les infos des modèles
    """
    try:
        response = requests.get(f"{host}/api/tags", timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data.get('models', [])
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération des modèles: {e}")
        return []


def format_model_size(size_bytes: int) -> str:
    """
    Formate la taille d'un modèle en unités lisibles

    Args:
        size_bytes: Taille en bytes

    Returns:
        Taille formatée (ex: "4.1 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def select_ollama_model_interactive(
    host: str,
    configured_model: str,
    logger=None
) -> Tuple[Optional[str], bool]:
    """
    Sélectionne un modèle Ollama de manière interactive avec navigation par flèches

    Args:
        host: URL du serveur Ollama
        configured_model: Modèle configuré (via .env ou --model)
        logger: Logger pour les messages

    Returns:
        Tuple (modèle_sélectionné, modèle_changé)
        - modèle_sélectionné: Nom du modèle choisi (ou None si erreur)
        - modèle_changé: True si différent du modèle configuré
    """
    print("\n" + "="*60)
    print("🔍 DÉTECTION DES MODÈLES OLLAMA")
    print("="*60)

    # Vérifier la connexion Ollama
    if not check_ollama_connection(host):
        print(f"\n❌ Impossible de se connecter à Ollama sur {host}")
        print("\n💡 Vérifiez que:")
        print("   1. Ollama est installé (https://ollama.ai)")
        print("   2. Le service Ollama est démarré")
        print("   3. L'URL est correcte (par défaut: http://localhost:11434)")
        return None, False

    # Récupérer les modèles disponibles
    models = get_available_models(host)

    if not models:
        print("\n❌ Aucun modèle Ollama détecté!")
        print("\n💡 Pour installer un modèle, utilisez:")
        print("   ollama pull llama2")
        print("   ollama pull mistral")
        print("   ollama pull codellama")
        return None, False

    # Extraire les noms de modèles
    model_names = [m['name'] for m in models]

    # Cas 1: Un seul modèle disponible
    if len(models) == 1:
        selected_model = model_names[0]
        model_size = format_model_size(models[0].get('size', 0))

        if configured_model and configured_model not in model_names:
            print(f"\n⚠️  Le modèle configuré '{configured_model}' n'est plus disponible")
            print(f"✓ Sélection automatique du seul modèle disponible: {selected_model} ({model_size})")
            if logger:
                logger.warning(f"Modèle '{configured_model}' introuvable, utilisation de '{selected_model}'")
            return selected_model, True
        else:
            print(f"\n✓ Un seul modèle disponible: {selected_model} ({model_size})")
            return selected_model, False

    # Cas 2: Plusieurs modèles - menu interactif
    print(f"\n✓ {len(models)} modèles Ollama détectés\n")

    # Vérifier si le modèle configuré existe
    model_changed = configured_model not in model_names
    if configured_model and model_changed:
        print(f"⚠️  Le modèle configuré '{configured_model}' n'est plus disponible")
        print("Veuillez en sélectionner un autre:\n")
        if logger:
            logger.warning(f"Modèle '{configured_model}' introuvable")
    elif configured_model:
        print(f"ℹ️  Modèle configuré: {configured_model}")
        print("Vous pouvez le changer ci-dessous:\n")

    # Préparer les options du menu avec tailles
    menu_options = []
    for model in models:
        name = model['name']
        size = format_model_size(model.get('size', 0))
        marker = " ✓" if name == configured_model else ""
        menu_options.append(f"{name} ({size}){marker}")

    # Créer le menu interactif
    try:
        terminal_menu = TerminalMenu(
            menu_options,
            title="Sélectionnez un modèle Ollama (↑↓ pour naviguer, Entrée pour valider):",
            cursor_index=model_names.index(configured_model) if configured_model in model_names else 0
        )

        menu_index = terminal_menu.show()

        if menu_index is None:
            # Utilisateur a annulé (Ctrl+C)
            print("\n⚠️  Sélection annulée")
            if configured_model in model_names:
                print(f"Utilisation du modèle configuré: {configured_model}")
                return configured_model, False
            else:
                return None, False

        selected_model = model_names[menu_index]
        model_size = format_model_size(models[menu_index].get('size', 0))

        print(f"\n✓ Modèle sélectionné: {selected_model} ({model_size})")

        return selected_model, selected_model != configured_model

    except Exception as e:
        print(f"\n❌ Erreur lors de la sélection: {e}")
        if configured_model in model_names:
            print(f"Utilisation du modèle configuré: {configured_model}")
            return configured_model, False
        return None, False


def main():
    """Point d'entrée principal de l'application"""
    parser = argparse.ArgumentParser(description='Terminal IA Autonome avec Ollama')
    parser.add_argument('--debug', action='store_true', help='Activer le mode debug')
    parser.add_argument('--model', type=str, help='Modèle Ollama à utiliser')
    args = parser.parse_args()

    # Configuration du logger
    logger = setup_logger(debug=args.debug)
    logger.info("Démarrage du Terminal IA...")

    # Phase 1: Optimisation hardware
    logger.info("Détection et optimisation du hardware...")
    hardware_optimizer = HardwareOptimizer(logger)

    # Afficher le rapport d'optimisation
    print("\n" + hardware_optimizer.get_optimization_report())

    # Chargement de la configuration
    settings = Settings()
    if args.model:
        settings.ollama_model = args.model

    # Appliquer les optimisations hardware
    hardware_optimizer.apply_optimizations(settings)

    # Phase: Vérification et démarrage automatique du serveur Ollama
    logger.info("Vérification du serveur Ollama...")
    ollama_manager = OllamaManager(settings.ollama_host, logger)

    is_running, message = ollama_manager.ensure_server_running()

    if not is_running:
        print(f"\n❌ ERREUR: {message}")
        logger.error(f"Impossible de démarrer Ollama: {message}")
        sys.exit(1)
    else:
        print(f"✅ {message}")
        logger.info(message)

    # Phase: Détection et sélection interactive des modèles Ollama
    selected_model, model_changed = select_ollama_model_interactive(
        host=settings.ollama_host,
        configured_model=settings.ollama_model,
        logger=logger
    )

    # Vérifier que le modèle a été sélectionné avec succès
    if selected_model is None:
        logger.error("Impossible de sélectionner un modèle Ollama")
        print("\n❌ Démarrage annulé: aucun modèle Ollama disponible")
        sys.exit(1)

    # Mettre à jour le modèle sélectionné
    if model_changed:
        logger.info(f"Changement de modèle: {settings.ollama_model} → {selected_model}")
    settings.ollama_model = selected_model

    # Phase 1: Initialisation du cache Ollama
    cache_config = CacheConfig()
    cache_manager = None
    if cache_config.cache_enabled:
        cache_manager = CacheManager(cache_config, logger)
        logger.info("✅ Cache Ollama initialisé")

    try:
        # Initialisation de l'interface terminal
        terminal = TerminalInterface(settings, logger, cache_manager=cache_manager)
        terminal.run()
    except KeyboardInterrupt:
        logger.info("\nArrêt du Terminal IA...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erreur fatale: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Configuration du multiprocessing pour Windows
    # IMPORTANT: Sur Windows, 'spawn' est obligatoire pour éviter les problèmes
    # Sur Linux/Mac, 'fork' est plus rapide mais 'spawn' est plus sûr
    try:
        # Vérifier si la méthode n'est pas déjà configurée
        current_method = multiprocessing.get_start_method(allow_none=True)
        if current_method is None:
            multiprocessing.set_start_method(constants.PARALLEL_PROCESS_START_METHOD, force=False)
        elif current_method != constants.PARALLEL_PROCESS_START_METHOD:
            # Méthode déjà configurée mais différente, forcer le changement
            multiprocessing.set_start_method(constants.PARALLEL_PROCESS_START_METHOD, force=True)
    except RuntimeError as e:
        # Déjà configuré avec la même méthode, continuer normalement
        pass
    except Exception as e:
        # Autre erreur lors de la configuration multiprocessing
        print(f"Attention: Impossible de configurer multiprocessing: {e}")
        print("L'application continuera avec les paramètres par défaut.")

    # Démarrer l'application
    main()
