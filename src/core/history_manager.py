"""
History Manager - Gestion de l'historique des commandes
Sauvegarde et charge l'historique de manière persistante
"""

import os
import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    Gestionnaire d'historique des commandes shell

    Fonctionnalités:
    - Historique persistant (fichier ~/.coter_history)
    - Navigation dans l'historique
    - Recherche de commandes
    - Statistiques d'utilisation
    """

    def __init__(self, history_file: Optional[str] = None, max_size: int = 10000):
        """
        Initialise le gestionnaire d'historique

        Args:
            history_file: Chemin du fichier d'historique (None = ~/.coter_history)
            max_size: Taille maximale de l'historique (défaut: 10000 commandes)
        """
        if history_file:
            self.history_file = Path(history_file).expanduser()
        else:
            self.history_file = Path.home() / ".coter_history"

        self.max_size = max_size
        self.history: List[Dict] = []
        self.current_index = -1  # Index pour navigation

        # Créer le fichier s'il n'existe pas
        if not self.history_file.exists():
            self.history_file.touch()
            logger.info(f"Fichier d'historique créé: {self.history_file}")

        # Charger l'historique existant
        self._load_history()

    def _load_history(self) -> None:
        """Charge l'historique depuis le fichier"""
        try:
            if self.history_file.stat().st_size == 0:
                # Fichier vide
                self.history = []
                return

            with open(self.history_file, 'r', encoding='utf-8') as f:
                # Format JSONL (une entrée par ligne)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            self.history.append(entry)
                        except json.JSONDecodeError:
                            # Ligne corrompue, ignorer
                            logger.warning(f"Ligne d'historique corrompue ignorée: {line[:50]}")

            logger.info(f"Historique chargé: {len(self.history)} commandes")

            # Limiter la taille
            if len(self.history) > self.max_size:
                self.history = self.history[-self.max_size:]
                self._save_history()

        except Exception as e:
            logger.error(f"Erreur lors du chargement de l'historique: {e}")
            self.history = []

    def _save_history(self) -> None:
        """Sauvegarde l'historique dans le fichier"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                for entry in self.history:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')

            logger.debug(f"Historique sauvegardé: {len(self.history)} commandes")

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'historique: {e}")

    def add_command(self, command: str, mode: str = "manual", success: bool = True) -> None:
        """
        Ajoute une commande à l'historique

        Args:
            command: La commande exécutée
            mode: Le mode shell (manual/auto/agent)
            success: Si la commande a réussi
        """
        if not command or not command.strip():
            return

        # Ne pas ajouter les doublons consécutifs
        if self.history and self.history[-1].get('command') == command:
            logger.debug("Doublon consécutif ignoré")
            return

        entry = {
            'command': command,
            'mode': mode,
            'timestamp': datetime.now().isoformat(),
            'success': success
        }

        self.history.append(entry)

        # Limiter la taille
        if len(self.history) > self.max_size:
            self.history = self.history[-self.max_size:]

        # Réinitialiser l'index de navigation
        self.current_index = len(self.history)

        # Sauvegarder
        self._save_history()

    def get_all(self) -> List[Dict]:
        """
        Retourne tout l'historique

        Returns:
            Liste des entrées d'historique
        """
        return self.history.copy()

    def get_recent(self, n: int = 10) -> List[Dict]:
        """
        Retourne les N dernières commandes

        Args:
            n: Nombre de commandes à retourner

        Returns:
            Liste des N dernières commandes
        """
        return self.history[-n:] if self.history else []

    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Recherche dans l'historique

        Args:
            query: Texte à rechercher
            limit: Nombre maximum de résultats

        Returns:
            Liste des commandes matchant la recherche
        """
        if not query:
            return []

        results = []
        query_lower = query.lower()

        # Rechercher en partant de la fin (plus récent en premier)
        for entry in reversed(self.history):
            if query_lower in entry['command'].lower():
                results.append(entry)
                if len(results) >= limit:
                    break

        return results

    def navigate_up(self) -> Optional[str]:
        """
        Navigation vers le haut (commande précédente)

        Returns:
            La commande précédente ou None
        """
        if not self.history:
            return None

        if self.current_index > 0:
            self.current_index -= 1
            return self.history[self.current_index]['command']

        return None

    def navigate_down(self) -> Optional[str]:
        """
        Navigation vers le bas (commande suivante)

        Returns:
            La commande suivante ou None
        """
        if not self.history:
            return None

        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]['command']
        else:
            # Fin de l'historique
            self.current_index = len(self.history)
            return ""

    def reset_navigation(self) -> None:
        """Réinitialise l'index de navigation à la fin"""
        self.current_index = len(self.history)

    def clear(self) -> None:
        """Efface tout l'historique"""
        self.history = []
        self.current_index = -1
        self._save_history()
        logger.info("Historique effacé")

    def remove_last(self) -> Optional[Dict]:
        """
        Supprime la dernière commande de l'historique

        Returns:
            La commande supprimée ou None
        """
        if self.history:
            removed = self.history.pop()
            self.current_index = len(self.history)
            self._save_history()
            return removed
        return None

    def get_statistics(self) -> Dict:
        """
        Retourne des statistiques sur l'historique

        Returns:
            Dict avec les statistiques
        """
        if not self.history:
            return {
                'total': 0,
                'by_mode': {},
                'success_rate': 0.0,
                'most_used': []
            }

        # Compter par mode
        by_mode = {}
        for entry in self.history:
            mode = entry.get('mode', 'unknown')
            by_mode[mode] = by_mode.get(mode, 0) + 1

        # Taux de succès
        successes = sum(1 for e in self.history if e.get('success', False))
        success_rate = (successes / len(self.history)) * 100 if self.history else 0

        # Commandes les plus utilisées
        command_counts = {}
        for entry in self.history:
            cmd = entry['command']
            command_counts[cmd] = command_counts.get(cmd, 0) + 1

        most_used = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'total': len(self.history),
            'by_mode': by_mode,
            'success_rate': success_rate,
            'most_used': most_used
        }

    def export_to_file(self, filepath: str, format: str = 'json') -> bool:
        """
        Exporte l'historique vers un fichier

        Args:
            filepath: Chemin du fichier de destination
            format: Format d'export ('json', 'txt', 'csv')

        Returns:
            True si succès
        """
        try:
            filepath = Path(filepath).expanduser()

            if format == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.history, f, indent=2, ensure_ascii=False)

            elif format == 'txt':
                with open(filepath, 'w', encoding='utf-8') as f:
                    for entry in self.history:
                        f.write(f"{entry['command']}\n")

            elif format == 'csv':
                import csv
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    if self.history:
                        writer = csv.DictWriter(f, fieldnames=self.history[0].keys())
                        writer.writeheader()
                        writer.writerows(self.history)

            else:
                logger.error(f"Format d'export inconnu: {format}")
                return False

            logger.info(f"Historique exporté vers {filepath} (format: {format})")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'export: {e}")
            return False

    def __len__(self) -> int:
        """Retourne le nombre de commandes dans l'historique"""
        return len(self.history)

    def __repr__(self) -> str:
        return f"HistoryManager(file={self.history_file}, size={len(self.history)})"

    def __str__(self) -> str:
        return f"Historique: {len(self.history)} commandes"
