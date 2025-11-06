# Data Directory

Ce dossier contient toutes les données runtime générées par CoTer.

## Structure

### `cache/`
Cache SQLite pour les réponses d'Ollama
- Format: SQLite database
- Objectif: Accélération des requêtes répétées (200x speedup)
- Gestion: LRU/LFU eviction policies

### `logs/`
Logs du système
- Format: Fichiers texte/JSON
- Rotation: Automatique selon configuration
- Niveaux: DEBUG, INFO, WARNING, ERROR, CRITICAL

### `history/`
Historique des commandes
- Format: JSONL (JSON Lines)
- Fichier: `.coter_history`
- Persistance: Entre sessions

## Configuration

Les chemins par défaut peuvent être modifiés dans `config/settings.py`:

```python
CACHE_DIR = Path("data/cache")
LOGS_DIR = Path("data/logs")
HISTORY_DIR = Path("data/history")
```

## Gitignore

Le contenu de ces dossiers est ignoré par git (données locales uniquement).
Seuls les fichiers `.gitignore` et ce `README.md` sont versionnés.

## Nettoyage

Pour nettoyer toutes les données:
```bash
rm -rf data/cache/* data/logs/* data/history/*
```

Ou utiliser les commandes intégrées:
```bash
/cache clear
history clear
```
