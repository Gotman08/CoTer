# CoTer - Shell Hybride avec IA Intégrée

<div align="center">

**Un vrai shell Linux avec 3 modes : MANUAL/AUTO/AGENT**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-Compatible-green.svg)](https://ollama.ai)
[![Platform](https://img.shields.io/badge/platform-Linux%20|%20Mac%20|%20Windows%20|%20Raspberry%20Pi-lightgrey.svg)](https://github.com)

[Installation](#-installation-rapide) •
[Utilisation](#-démarrage-rapide) •
[Documentation](docs/) •
[Guides](docs/guides/)

</div>

---

## 🎯 Qu'est-ce que CoTer ?

**CoTer** est un shell hybride qui fonctionne comme bash en mode normal, avec la possibilité d'activer l'IA à la demande.

### Les 3 Modes

```
⌨️  MODE MANUAL (défaut)  → Shell direct comme bash - Pas d'IA, pas de latence
🤖 MODE AUTO             → Langage naturel via Ollama - "liste les fichiers Python"
🏗️  MODE AGENT            → Projets autonomes - "crée-moi une API FastAPI"
```

### Pourquoi utiliser CoTer ?

- ✅ **Shell complet** : Remplace bash/zsh, utilisable comme shell de connexion (`chsh`)
- ⚡ **Rapide** : Mode MANUAL sans latence IA
- 🤖 **IA à la demande** : Activez `/auto` seulement quand nécessaire
- 📜 **Historique unifié** : Un seul historique pour tous les modes
- 🔒 **Sécurisé** : Validation des commandes, confirmations pour opérations sensibles
- 🏠 **Raspberry Pi ready** : Optimisé pour systèmes avec RAM limitée

---

## 📦 Installation Rapide

### Prérequis

```bash
# Python 3.8+
python3 --version

# Ollama (pour les modes AUTO/AGENT)
curl https://ollama.ai/install.sh | sh
```

### Installation

```bash
# 1. Cloner le repository
git clone https://github.com/votre-compte/CoTer.git
cd CoTer

# 2. Installer CoTer
sudo ./scripts/install.sh

# 3. Lancer CoTer
coter
```

**Installation détaillée** : Voir [docs/guides/installation.md](docs/guides/installation.md)

---

## 🚀 Démarrage Rapide

### Mode MANUAL (défaut)
Shell direct comme bash - pas d'IA :

```bash
⌨️ [~/projects]
> ls -la | grep py
> cd /tmp && pwd
> export PATH=$PATH:/new/path
```

**Commandes intégrées** : `cd`, `pwd`, `history`, `clear`, `help`, `env`, `export`, `echo`

### Mode AUTO
Basculer vers langage naturel :

```bash
> /auto

🤖 [~/projects]
> liste les fichiers Python de plus de 100 lignes
📝 Commande générée: find . -name "*.py" -exec wc -l {} \; | awk '$1 > 100'
```

### Mode AGENT
Créer des projets complets :

```bash
> /agent crée-moi une API REST avec FastAPI et authentification

🏗️ Mode AGENT : Analyse en cours...

📋 Plan (4 étapes):
  1. Créer structure projet
  2. Configurer FastAPI + JWT
  3. Implémenter endpoints
  4. Ajouter tests

Voulez-vous lancer l'exécution? (oui/non): _
```

**Guide complet** : Voir [docs/guides/agent-mode.md](docs/guides/agent-mode.md)

---

## 🎛️ Commandes Spéciales

```bash
/manual     # Basculer en mode MANUAL (shell direct)
/auto       # Basculer en mode AUTO (langage naturel)
/agent      # Lancer le mode AGENT (projets)
/status     # Afficher statut et statistiques
/cache      # Gérer le cache Ollama
help        # Aide des commandes builtins
history     # Historique des commandes
```

---

## 📚 Documentation Complète

Toute la documentation est dans [docs/](docs/) :

### 📖 Guides Utilisateur

- [**Guide d'Installation**](docs/guides/installation.md) - Installation détaillée
- [**Mode Agent**](docs/guides/agent-mode.md) - Créer des projets autonomes
- [**Configuration Ollama**](docs/guides/ollama-setup.md) - Setup Ollama
- [**WSL sous Windows**](docs/guides/wsl-setup.md) - Utiliser sous WSL

### 🔧 Référence Technique

- [**Multiprocessing**](docs/reference/multiprocessing.md) - Parallélisme et optimisations

### 🛠️ Pour les Développeurs

- [**Architecture**](docs/development/refactoring.md) - Structure du code
- [**Tests**](docs/development/test-results.md) - Rapports de tests

### 📋 Changelog

- [**Historique**](docs/changelog/CHANGELOG.md) - Toutes les versions

---

## ⚙️ Configuration

Configuration dans `config/shell_config.yaml` :

```yaml
# Prompt
prompt:
  show_user: true
  show_git_branch: true

# Historique
history:
  max_size: 10000
  file: "~/.coter_history"

# Cache Ollama
cache:
  enabled: true
  ttl_hours: 72
  max_size_mb: 200
```

**Configuration complète** : Voir [docs/reference/configuration.md](docs/reference/configuration.md)

---

## 🔒 Sécurité

CoTer intègre plusieurs couches de sécurité :

- ✅ **Validation des commandes** : Détection des commandes dangereuses
- ✅ **Évaluation des risques** : Score 0-100 pour chaque commande
- ✅ **Confirmations** : Demande confirmation pour opérations sensibles
- ✅ **Snapshots/Rollback** : Restauration en cas d'échec (mode AGENT)
- ✅ **Logging** : Traçabilité complète des opérations

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez [docs/development/contributing.md](docs/development/contributing.md)

---

## 📄 Licence

MIT - Voir [LICENSE](LICENSE)

---

## 🔗 Liens Utiles

- **Documentation** : [docs/](docs/)
- **Scripts** : [scripts/](scripts/)
- **Configuration** : [config/](config/)
- **Tests** : [tests/](tests/)

---

**Créé par CoTer - Terminal IA Autonome**
