# CoTer - Shell Hybride Linux avec IA Intégrée

<div align="center">

**Un vrai shell Linux avec modes MANUAL/AUTO/AGENT - L'IA à la demande uniquement**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-Compatible-green.svg)](https://ollama.ai)
[![Platform](https://img.shields.io/badge/platform-Linux%20|%20Mac%20|%20Windows%20|%20WSL%20|%20Raspberry%20Pi-lightgrey.svg)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[Fonctionnalités](#-fonctionnalités) •
[Installation](#-installation-rapide) •
[Utilisation](#-utilisation) •
[Modes](#-les-3-modes-du-shell) •
[Configuration](#-configuration)

</div>

---

## 🎯 Présentation

**CoTer** est un **shell hybride Linux** qui fonctionne comme bash en mode normal, avec la possibilité d'activer l'IA à la demande. Utilisez-le comme shell principal sur votre système !

### 💡 Le Concept

CoTer n'est **PAS** un simple wrapper IA qui parse tout via Ollama. C'est un **vrai shell** avec 3 modes :

```
⌨️  MODE MANUAL (défaut)  → Shell direct comme bash (pas d'IA)
🤖 MODE AUTO             → Langage naturel via Ollama
🏗️  MODE AGENT            → Projets autonomes multi-étapes
```

### ✨ Pourquoi CoTer ?

| Avantage | Description |
|----------|-------------|
| 🚀 **Shell complet** | Remplace bash/zsh, pas juste un assistant |
| ⚡ **Rapide en MANUAL** | Pas de latence IA quand vous n'en avez pas besoin |
| 🤖 **IA à la demande** | Activez l'IA seulement quand nécessaire (`/auto`) |
| 📜 **Historique unifié** | Un seul historique pour tous les modes |
| 🏠 **Shell de connexion** | Utilisable comme shell par défaut (`chsh`) |
| 🍰 **Raspberry Pi ready** | Optimisé pour systèmes avec RAM limitée |

---

## 🚀 Les 3 Modes du Shell

### ⌨️ Mode MANUAL (par défaut)

**Shell direct comme bash** - Aucune IA, exécution immédiate.

```bash
⌨️ [~/projects]
> ls -la | grep py
> cd /tmp && pwd
> export PATH=$PATH:/new/path
> echo "Hello $USER"
```

**Fonctionnalités** :
- Pipes, redirections (`|`, `>`, `>>`, `<`)
- Chaînage de commandes (`&&`, `||`, `;`)
- Variables d'environnement (`$VAR`)
- Commandes builtins (cd, pwd, history, help, etc.)
- **Aucune latence** - Exécution native

### 🤖 Mode AUTO

**Langage naturel via Ollama** - L'IA parse vos demandes.

```bash
# Basculer en mode AUTO
> /auto

🤖 [~/projects]
> liste les fichiers Python
📝 Commande générée: ls -la *.py
✅ Commande exécutée avec succès

🤖 [~/projects]
> montre les 5 plus gros dossiers
📝 Commande générée: du -sh * | sort -h | tail -5
```

**Quand l'utiliser** :
- Vous ne connaissez pas la syntaxe exacte
- Requêtes complexes (find, awk, sed...)
- Découverte de commandes

### 🏗️ Mode AGENT

**Projets autonomes multi-étapes** - L'IA crée des projets complets.

```bash
> /agent crée-moi une API FastAPI avec authentification JWT

🏗️ Mode AGENT : Analyse en cours...

📋 Plan généré (8 étapes) :
  1. Créer la structure du projet
  2. Fichier requirements.txt
  3. Modèles Pydantic
  4. Routes d'authentification
  5. Middleware JWT
  6. Endpoints API
  7. Tests unitaires
  8. Documentation README

Voulez-vous lancer l'exécution? (oui/non): oui

[1/8] 📁 Créer la structure du projet...
      ✅ 5 dossiers créés
[2/8] 📝 Fichier requirements.txt...
      ✅ Fichier créé: requirements.txt (12 lignes)
...
```

**Features** :
- Planification intelligente multi-étapes
- Exécution parallèle (multiprocessing)
- Auto-correction automatique (retry jusqu'à 3x)
- Snapshots avant modifications
- Rollback en cas d'échec

---

## 🎨 Fonctionnalités

### Core Shell Features

| Fonctionnalité | Description | Statut |
|----------------|-------------|--------|
| 🐚 **Shell complet** | Remplace bash/zsh comme shell principal | ✅ |
| ⌨️ **Mode MANUAL** | Exécution directe sans IA (rapide!) | ✅ |
| 🤖 **Mode AUTO** | Langage naturel via Ollama | ✅ |
| 🏗️ **Mode AGENT** | Projets autonomes multi-étapes | ✅ |
| 📜 **Historique persistant** | `~/.coter_history` avec recherche | ✅ |
| 🎨 **Prompt personnalisable** | Couleurs, Git branch, user@host | ✅ |
| 🔧 **Commandes builtins** | cd, pwd, history, help, env, export | ✅ |
| 🚀 **Shell de connexion** | Utilisable avec `chsh` | ✅ |

### AI/Automation Features

| Fonctionnalité | Description | Statut |
|----------------|-------------|--------|
| 🤖 **LLM Local** | Ollama pour traitement 100% privé | ✅ |
| 🔄 **Multiprocessing** | Vrai parallélisme (bypass GIL Python) | ✅ |
| 💾 **Cache SQLite** | Réponses instantanées (200x speedup) | ✅ |
| 🔁 **Auto-correction** | Retry automatique jusqu'à 3x | ✅ |
| 📸 **Snapshots/Rollback** | Protection Git-like des projets | ✅ |
| 🛡️ **Sécurité** | Validation, whitelist/blacklist | ✅ |
| 📊 **Hardware Optimizer** | Auto-détection CPU/RAM, tuning | ✅ |

---

## 📦 Installation Rapide

### Prérequis

- **Python 3.8+** (testé sur 3.12.3)
- **Ollama** installé ([ollama.ai](https://ollama.ai))
- **Linux, macOS, ou WSL** (Windows natif supporté mais moins optimal)

### Installation Standard

```bash
# 1. Cloner le repository
git clone https://github.com/VOTRE_USERNAME/CoTer.git
cd CoTer

# 2. Créer environnement virtuel (recommandé)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac/WSL
# ou
venv\Scripts\activate     # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer CoTer
python main.py
```

### Installation comme Shell Principal (Linux/Mac)

```bash
# 1. Installation via le script
chmod +x install.sh
sudo ./install.sh

# 2. Ajouter CoTer aux shells autorisés
echo "/usr/local/bin/coter" | sudo tee -a /etc/shells

# 3. Définir comme shell par défaut
chsh -s /usr/local/bin/coter

# 4. Se reconnecter
# CoTer sera maintenant votre shell de connexion!
```

### Installation Raspberry Pi

```bash
# Installation optimisée pour Raspberry Pi
./install.sh --raspberry-pi

# Configuration automatique:
# - Mode basse consommation
# - Cache limité (50 MB max)
# - Optimisations CPU
```

---

## 🎮 Utilisation

### Démarrage

```bash
python main.py
```

**Au démarrage** :
1. Ollama démarre automatiquement (si nécessaire)
2. Sélection interactive du modèle (↑↓ pour naviguer)
3. Shell démarre en **mode MANUAL** par défaut

```
╔════════════════════════════════════════════════════════════╗
║  CoTer - Terminal IA Autonome                              ║
║  Version 1.0                                               ║
╠════════════════════════════════════════════════════════════╣
║  Mode: MANUAL                                              ║
║  Commandes: /manual /auto /agent /help /quit              ║
╚════════════════════════════════════════════════════════════╝

Modèle: llama2:latest | Host: http://localhost:11434
⌨️  Mode: MANUAL - Mode Shell Direct - Commandes exécutées sans IA

Commandes: /manual /auto /agent /help /quit
Tapez /help pour l'aide complète

⌨️ [~/projects]
>
```

### Commandes Slash

Les commandes slash fonctionnent dans **tous les modes** :

```bash
# Gestion des modes
/manual       # Basculer en mode MANUAL (shell direct)
/auto         # Basculer en mode AUTO (IA activée)
/agent <req>  # Lancer un projet autonome
/status       # Voir le statut actuel du shell

# Historique et aide
/history      # Afficher l'historique (20 dernières commandes)
/help         # Aide complète
/clear        # Effacer l'historique IA

# Configuration
/models       # Changer de modèle Ollama
/cache        # Statistiques du cache
/hardware     # Infos hardware et optimisations

# Système
/info         # Informations système
/quit         # Quitter CoTer
```

### Commandes Builtins

Les commandes builtins fonctionnent en **mode MANUAL** :

```bash
# Navigation
cd <dir>      # Changer de répertoire
pwd           # Afficher le répertoire courant

# Historique
history       # Afficher l'historique complet
history search <terme>   # Rechercher dans l'historique
history stats            # Statistiques d'historique
history clear            # Effacer l'historique

# Environnement
env           # Afficher toutes les variables
env <VAR>     # Afficher une variable spécifique
export VAR=value  # Exporter une variable

# Utilitaires
echo <text>   # Afficher du texte (supporte $VAR)
clear         # Effacer l'écran (alias: cls)
help          # Aide sur les commandes builtins
exit          # Quitter (alias: quit)
```

### Exemples d'Utilisation

#### 1. Workflow quotidien (Mode MANUAL)

```bash
⌨️ [~]
> cd projects/myapp

⌨️ [~/projects/myapp]
> ls -la
# Affiche les fichiers

⌨️ [~/projects/myapp]
> git status
# Status git

⌨️ [~/projects/myapp]
> docker ps | grep mysql
# Containers MySQL en cours
```

#### 2. Découverte de commandes (Mode AUTO)

```bash
⌨️ [~/projects]
> /auto

🤖 [~/projects]
> trouve tous les fichiers Python modifiés dans les 7 derniers jours
📝 Commande générée: find . -name "*.py" -mtime -7
✅ Exécution...

🤖 [~/projects]
> compte les lignes de code dans tous les fichiers Python
📝 Commande générée: find . -name "*.py" -exec wc -l {} + | tail -1
```

#### 3. Création de projet (Mode AGENT)

```bash
⌨️ [~/projects]
> /agent crée un bot Discord en Python avec commandes !ping et !hello

🏗️ Mode AGENT : Analyse en cours...

📋 Plan généré (6 étapes) :
  1. Structure du projet bot_discord/
  2. requirements.txt (discord.py)
  3. config.py pour le token
  4. bot.py avec event handlers
  5. commands/ping.py
  6. commands/hello.py

Voulez-vous lancer l'exécution? (oui/non): oui

[1/6] 📁 Structure du projet bot_discord/...
      ✅ 3 dossiers créés
[2/6] 📝 requirements.txt...
      ✅ Fichier créé (5 lignes)
...

✨ Projet créé dans: ~/projects/bot_discord
```

---

## ⚙️ Configuration

### Fichier de configuration

Personnalisez CoTer via [`config/shell_config.yaml`](config/shell_config.yaml) :

```yaml
# Mode de démarrage par défaut
default_mode: manual  # Options: manual, auto, agent

# Configuration du prompt
prompt:
  enable_colors: true
  show_user: false
  show_host: false
  show_git: true      # Afficher la branche Git
  multiline: true

# Historique
history:
  max_size: 10000
  ignore_duplicates: true

# Shell
shell:
  command_timeout: 30
  confirm_dangerous_commands: true

# IA/Ollama
ai:
  auto_detect_complex_projects: true
  ollama_timeout: 60

# Cache
cache:
  enabled: true
  eviction_policy: lru  # Options: lru, lfu, fifo
  max_entries: 1000

# Sécurité
security:
  blocked_commands:
    - "rm -rf /"
    - "dd if="
  enable_validation: true
```

### Variables d'environnement

Créer un fichier [`.env`](.env) :

```bash
# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2:latest

# Cache
CACHE_ENABLED=true
CACHE_MAX_SIZE=500  # MB
CACHE_EVICTION_POLICY=lru

# Agent
AGENT_ENABLED=true
AGENT_MAX_WORKERS=4

# Logging
LOG_LEVEL=INFO
```

---

## 🧪 Tests et Validation

### Tests automatisés

```bash
# Lancer tous les tests
python -m pytest tests/

# Tests spécifiques
python -m pytest tests/test_shell_modes.py
python -m pytest tests/test_history.py
python -m pytest tests/test_builtins.py
```

### Tests manuels

```bash
# Test mode MANUAL
> cd /tmp
> pwd
> echo "test"
> ls -la | grep test

# Test mode AUTO
> /auto
> liste les processus python
> /manual

# Test mode AGENT
> /agent crée un script hello.py qui affiche "Hello World"
```

---

## 🏗️ Architecture

### Structure du projet

```
CoTer/
├── main.py                      # Point d'entrée
├── config/
│   ├── settings.py              # Configuration générale
│   ├── shell_config.yaml        # Config du shell
│   └── prompts.py               # Prompts IA
├── src/
│   ├── core/                    # Modules core du shell
│   │   ├── shell_engine.py      # Gestion des modes
│   │   ├── history_manager.py   # Historique persistant
│   │   ├── builtins.py          # Commandes builtins
│   │   └── prompt_manager.py    # Personnalisation prompt
│   ├── modules/                 # Modules IA/Agent
│   │   ├── ollama_client.py     # Client Ollama
│   │   ├── command_executor.py  # Exécution commandes
│   │   ├── autonomous_agent.py  # Mode agent
│   │   └── command_parser.py    # Parsing LN → commandes
│   ├── utils/                   # Utilitaires
│   │   ├── cache_manager.py     # Cache SQLite
│   │   ├── auto_corrector.py    # Auto-correction
│   │   ├── rollback_manager.py  # Snapshots/rollback
│   │   └── hardware_optimizer.py # Optimisations hardware
│   └── terminal_interface.py    # Interface principale
├── tests/                       # Tests unitaires
└── docs/                        # Documentation
```

### Flow d'exécution

```
User Input
    ↓
┌─── Mode MANUAL? ───┐
│   Oui                  │   Non
│   ↓                    │   ↓
│ Builtins?              │ Mode AUTO?
│   Oui → Execute        │   Oui → Ollama Parse
│   Non → subprocess     │   Non → Mode AGENT → Plan + Execute
│   ↓                    │   ↓
└─── History + Display ──┘
```

---

## 🚧 Roadmap

### ✅ Implémenté (v1.0)

- [x] Shell hybride 3 modes (MANUAL/AUTO/AGENT)
- [x] Historique persistant avec recherche
- [x] Commandes builtins essentielles
- [x] Prompt personnalisable avec couleurs
- [x] Configuration via YAML
- [x] Mode agent avec multiprocessing
- [x] Cache SQLite pour Ollama
- [x] Auto-correction et retry
- [x] Snapshots et rollback
- [x] Optimisations Raspberry Pi

### 🔄 En cours (v1.1)

- [ ] Auto-complétion avec TAB (prompt_toolkit)
- [ ] Gestion avancée des signaux (Ctrl+C/D/Z)
- [ ] Tests unitaires complets (>80% coverage)
- [ ] Documentation API complète

### 🔮 Futur (v2.0)

- [ ] Plugin system pour extensions
- [ ] Thèmes de prompt personnalisables
- [ ] Intégration tmux/screen
- [ ] Support d'autres LLMs (GPT-4, Claude)
- [ ] Web UI optionnelle

---

## 🤝 Contribution

Les contributions sont bienvenues ! Voici comment contribuer :

1. **Fork** le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une **Pull Request**

### Guidelines

- Suivre PEP 8 pour le style Python
- Ajouter des tests pour les nouvelles fonctionnalités
- Mettre à jour la documentation
- Utiliser des messages de commit clairs

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 🙏 Remerciements

- **Ollama** pour le LLM local
- **Anthropic** pour l'inspiration du design
- La communauté Python pour les excellentes librairies
- Tous les contributeurs !

---

## 📞 Support

- **Issues** : [GitHub Issues](https://github.com/VOTRE_USERNAME/CoTer/issues)
- **Discussions** : [GitHub Discussions](https://github.com/VOTRE_USERNAME/CoTer/discussions)
- **Documentation** : [Wiki](https://github.com/VOTRE_USERNAME/CoTer/wiki)

---

<div align="center">

**Fait avec ❤️ pour la communauté open-source**

[⬆ Retour en haut](#coter---shell-hybride-linux-avec-ia-intégrée)

</div>
