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
from src.terminal.rich_console import get_console
from src.terminal import rich_components
from src.utils.logger import setup_logger
from src.utils import HardwareOptimizer, CacheManager, OllamaManager, UserConfigManager
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
    console = get_console()
    try:
        response = requests.get(f"{host}/api/tags", timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data.get('models', [])
    except requests.exceptions.RequestException as e:
        console.error(f"Erreur lors de la récupération des modèles: {e}")
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
    console = get_console()

    # Titre sobre
    console.print()
    console.print_panel(
        "[bold cyan]Détection des Modèles Ollama[/bold cyan]",
        style="cyan"
    )

    # Vérifier la connexion Ollama
    if not check_ollama_connection(host):
        error_msg = f"Impossible de se connecter à Ollama sur {host}\n\n"
        error_msg += "Vérifiez que:\n"
        error_msg += "  1. Ollama est installé (https://ollama.ai)\n"
        error_msg += "  2. Le service Ollama est démarré\n"
        error_msg += "  3. L'URL est correcte"

        console.print()
        console.print(rich_components.create_error_panel(error_msg, "Connexion Impossible"))
        return None, False

    # Récupérer les modèles disponibles
    models = get_available_models(host)

    if not models:
        error_msg = "Aucun modèle Ollama détecté!\n\n"
        error_msg += "Pour installer un modèle, utilisez:\n"
        error_msg += "  [dim]ollama pull llama2[/dim]\n"
        error_msg += "  [dim]ollama pull mistral[/dim]\n"
        error_msg += "  [dim]ollama pull codellama[/dim]"

        console.print()
        console.print(rich_components.create_error_panel(error_msg, "Aucun Modèle"))
        return None, False

    # Extraire les noms de modèles
    model_names = [m['name'] for m in models]

    # Cas 1: Un seul modèle disponible
    if len(models) == 1:
        selected_model = model_names[0]
        model_size = format_model_size(models[0].get('size', 0))

        if configured_model and configured_model not in model_names:
            console.print()
            console.warning(f"Le modèle configuré '{configured_model}' n'est plus disponible")
            console.success(f"Sélection automatique: {selected_model} ({model_size})")
            if logger:
                logger.warning(f"Modèle '{configured_model}' introuvable, utilisation de '{selected_model}'")
            return selected_model, True
        else:
            console.print()
            console.info(f"Modèle unique détecté: {selected_model} ({model_size})")
            return selected_model, False

    # Cas 2: Plusieurs modèles - menu interactif
    console.print()
    console.info(f"{len(models)} modèles Ollama détectés")
    console.print()

    # Vérifier si le modèle configuré existe
    model_changed = configured_model not in model_names
    if configured_model and model_changed:
        console.warning(f"Le modèle configuré '{configured_model}' n'est plus disponible")
        console.print("[dim]Veuillez en sélectionner un autre:[/dim]")
        console.print()
        if logger:
            logger.warning(f"Modèle '{configured_model}' introuvable")
    elif configured_model:
        console.print(f"[label]Modèle configuré:[/label] [info]{configured_model}[/info]")
        console.print("[dim]Vous pouvez le changer ci-dessous:[/dim]")
        console.print()

    # Préparer les options du menu avec tailles
    menu_options = []
    for model in models:
        name = model['name']
        size = format_model_size(model.get('size', 0))
        marker = " ●" if name == configured_model else ""
        menu_options.append(f"{name} ({size}){marker}")

    # Créer le menu interactif
    try:
        terminal_menu = TerminalMenu(
            menu_options,
            title="Sélectionnez un modèle (↑↓ pour naviguer, Entrée pour valider):",
            cursor_index=model_names.index(configured_model) if configured_model in model_names else 0
        )

        menu_index = terminal_menu.show()

        if menu_index is None:
            # Utilisateur a annulé (Ctrl+C)
            console.print()
            console.warning("Sélection annulée")
            if configured_model in model_names:
                console.info(f"Utilisation du modèle configuré: {configured_model}")
                return configured_model, False
            else:
                return None, False

        selected_model = model_names[menu_index]
        model_size = format_model_size(models[menu_index].get('size', 0))

        console.print()
        console.success(f"Modèle sélectionné: {selected_model} ({model_size})")

        return selected_model, selected_model != configured_model

    except Exception as e:
        console.print()
        console.error(f"Erreur lors de la sélection: {e}")
        if configured_model in model_names:
            console.info(f"Utilisation du modèle configuré: {configured_model}")
            return configured_model, False
        return None, False


def main():
    """Point d'entrée principal de l'application"""
    parser = argparse.ArgumentParser(description='Terminal IA Autonome avec Ollama')
    parser.add_argument('--debug', action='store_true', help='Activer le mode debug')
    parser.add_argument('--model', type=str, help='Modèle Ollama à utiliser')
    args = parser.parse_args()

    console = get_console()

    # Configuration du logger
    logger = setup_logger(debug=args.debug)
    logger.info("Démarrage du Terminal IA...")

    # Phase 1: Optimisation hardware
    logger.info("Détection et optimisation du hardware...")
    hardware_optimizer = HardwareOptimizer(logger)

    # Afficher le rapport d'optimisation avec Rich
    console.print()

    # Utiliser la méthode get_optimization_report_dict() pour obtenir les infos
    hardware_info = hardware_optimizer.get_optimization_report_dict()

    hardware_table = rich_components.create_hardware_table(hardware_info)
    console.print(hardware_table)

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
        console.print()
        console.error(f"ERREUR: {message}")
        logger.error(f"Impossible de démarrer Ollama: {message}")
        sys.exit(1)
    else:
        console.print()
        console.success(message)
        logger.info(message)

    # Phase: Initialisation de la configuration utilisateur
    user_config = UserConfigManager()
    logger.info(f"Configuration utilisateur: {user_config.get_config_path()}")

    # Utiliser le dernier modèle utilisé ou celui dans settings.ollama_model
    last_model = user_config.get_last_model()
    configured_model = last_model if last_model else settings.ollama_model
    logger.info(f"Modèle configuré: {configured_model}")

    # Phase: Détection et sélection interactive des modèles Ollama
    selected_model, model_changed = select_ollama_model_interactive(
        host=settings.ollama_host,
        configured_model=configured_model,
        logger=logger
    )

    # Vérifier que le modèle a été sélectionné avec succès
    if selected_model is None:
        logger.error("Impossible de sélectionner un modèle Ollama")
        console.print()
        console.error("Démarrage annulé: aucun modèle Ollama disponible")
        sys.exit(1)

    # Mettre à jour le modèle sélectionné
    if model_changed:
        logger.info(f"Changement de modèle: {configured_model} → {selected_model}")
    settings.ollama_model = selected_model

    # Sauvegarder le modèle sélectionné dans la configuration utilisateur
    user_config.save_last_model(selected_model)
    logger.info(f"Modèle sauvegardé: {selected_model}")

    # Phase 1: Initialisation du cache Ollama
    cache_config = CacheConfig()
    cache_manager = None
    if cache_config.cache_enabled:
        cache_manager = CacheManager(cache_config, logger)
        logger.info("Cache Ollama initialisé")

    try:
        # Initialisation de l'interface terminal
        terminal = TerminalInterface(
            settings,
            logger,
            cache_manager=cache_manager,
            user_config=user_config
        )
        terminal.run()
    except KeyboardInterrupt:
        console.print()
        console.info("Arrêt du Terminal IA...")
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
        console = get_console()
        console.warning(f"Impossible de configurer multiprocessing: {e}")
        console.print("[dim]L'application continuera avec les paramètres par défaut.[/dim]")

    # Démarrer l'application
    main()
