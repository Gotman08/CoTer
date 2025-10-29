# Guide du Mode Agent Autonome

## Vue d'ensemble

Le mode agent autonome transforme votre Terminal IA en un assistant capable de créer des projets complets automatiquement. Au lieu de taper des commandes individuelles, vous décrivez ce que vous voulez et l'IA planifie et exécute toutes les étapes nécessaires.

## Comment ça marche

### 1. Détection Automatique

Quand vous faites une demande complexe (comme "crée-moi une API REST"), l'IA détecte automatiquement qu'il s'agit d'un projet et propose d'activer le mode agent autonome.

```
🤖 [/home/user]
> crée-moi une API REST avec FastAPI et authentification JWT

📦 Projet complexe détecté: fastapi_jwt
🤖 Activation du mode agent autonome...

Utiliser le mode agent autonome? (oui/non): oui
```

### 2. Génération du Plan

L'IA analyse votre demande et génère un plan détaillé :

```
╔════════════════════════════════════════════════════════════╗
║           PLAN D'EXÉCUTION AUTONOME                        ║
╠════════════════════════════════════════════════════════════╣
║ Projet: fastapi-jwt-api                                   ║
║ Description: API FastAPI avec authentification JWT        ║
║ Temps estimé: ~15 minutes                                 ║
╠════════════════════════════════════════════════════════════╣
║ Étape 1: 📁 Créer la structure de dossiers                ║
║ Étape 2: 📝 Générer app/main.py                           ║
║ Étape 3: 📝 Créer app/core/security.py                    ║
║ Étape 4: 📝 Générer app/routers/auth.py                   ║
║ Étape 5: 📝 Créer app/models/user.py                      ║
║ Étape 6: 📝 Générer requirements.txt                      ║
║ Étape 7: 📝 Créer README.md                               ║
║ Étape 8: 📦 Commit initial du projet                      ║
╚════════════════════════════════════════════════════════════╝
```

### 3. Validation et Exécution

Vous validez le plan, puis l'IA l'exécute étape par étape :

```
Voulez-vous lancer l'exécution? (oui/non/modifier): oui

🚀 Lancement de l'exécution autonome...

[1/8] 📁  Créer la structure de dossiers...
      ✅ 5 dossiers créés

[2/8] 📝  Générer app/main.py...
      🤖 Génération du code via Ollama...
      ✅ Fichier créé: app/main.py (145 lignes)

[3/8] 📝  Créer app/core/security.py...
      ✅ Fichier créé: app/core/security.py (89 lignes)

...

✅ Exécution terminée avec succès!
✨ Projet créé dans: /home/user/fastapi-jwt-api

📊 Résumé: 8 étapes exécutées
```

## Utilisation

### Méthode 1: Détection Automatique (Recommandé)

Tapez simplement votre demande en langage naturel :

```bash
> crée-moi un bot Discord
> génère une application Flask avec authentification
> fais-moi un script d'analyse de données avec Pandas
> crée un projet FastAPI REST API
```

L'IA détectera automatiquement qu'il s'agit d'un projet complexe et proposera le mode agent.

### Méthode 2: Commande Explicite

Utilisez la commande `/agent` :

```bash
> /agent crée-moi une API REST avec FastAPI
```

### Templates Disponibles

Listez les templates prédéfinis :

```bash
> /templates
```

Templates disponibles :
- **flask_basic** - Application web Flask basique
- **fastapi_rest** - API REST avec FastAPI
- **fastapi_jwt** - API FastAPI avec authentification JWT
- **cli_tool** - Outil en ligne de commande
- **data_analysis** - Projet d'analyse de données
- **discord_bot** - Bot Discord
- **web_scraper** - Web scraper

## Commandes de Contrôle

Pendant l'exécution, vous pouvez :

- **Ctrl+C** - Arrêter l'agent à tout moment
- **/pause** - Mettre en pause l'exécution
- **/resume** - Reprendre l'exécution
- **/stop** - Arrêter définitivement l'agent

## Fonctionnalités

### 🤖 Génération de Code Intelligente

L'IA génère du code propre et fonctionnel pour chaque fichier en utilisant les meilleures pratiques :

- Code commenté et documenté
- Structure professionnelle
- Gestion d'erreurs
- Configuration via variables d'environnement
- Tests (si demandé)

### 📁 Structure Complète

L'agent crée automatiquement :

- Dossiers et sous-dossiers
- Fichiers de code (.py, .js, etc.)
- Configuration (requirements.txt, .env.example)
- Documentation (README.md)
- Git (.gitignore)

### 📦 Gestion Git Automatique

- Initialisation du dépôt Git
- Création de .gitignore approprié
- Commits automatiques avec messages intelligents
- Messages générés par l'IA contextuellement

### 🔄 Exécution en Temps Réel

Suivi de la progression en direct :

```
[3/8] 📝  Générer app/main.py...
      🤖 Génération du code via Ollama...
      ✅ Fichier créé: app/main.py (145 lignes)
```

## Exemples d'Utilisation

### Exemple 1: API REST Simple

```
> crée-moi une API REST avec FastAPI

📦 Projet complexe détecté: fastapi_rest
Utiliser le mode agent autonome? (oui): oui

[Plan généré avec 6 étapes]

Voulez-vous lancer l'exécution? (oui): oui

✅ Exécution terminée avec succès!
✨ Projet créé dans: /home/user/fastapi-rest-api
```

### Exemple 2: Bot Discord Avancé

```
> fais-moi un bot Discord avec commandes de modération

📦 Projet complexe détecté: discord_bot

[Plan avec 10 étapes incluant:]
- Structure bot Discord
- Cogs pour modération
- Système de permissions
- Configuration
- Documentation

✅ Projet créé et prêt à l'emploi!
```

### Exemple 3: Application Data Science

```
> crée un projet d'analyse de données avec Pandas et Matplotlib
  pour analyser des fichiers CSV

📦 Projet complexe détecté: data_analysis

[Génère:]
- Notebooks Jupyter
- Scripts de chargement de données
- Visualisations
- Rapports automatiques
```

## Configuration

### Paramètres dans .env

```env
# Agent autonome
AGENT_MAX_STEPS=50              # Max d'étapes par plan
AGENT_MAX_DURATION=30           # Timeout en minutes
AGENT_PAUSE_STEPS=0.5           # Pause entre étapes (secondes)

# Génération de code
CODE_GEN_MAX_FILE_SIZE=100000   # Taille max des fichiers générés

# Git
GIT_AUTO_INIT=true              # Init git auto
GIT_AUTO_COMMIT=true            # Commits auto
```

### Paramètres dans config/settings.py

Vous pouvez désactiver le mode agent :

```python
self.agent_enabled = False
```

## Limites de Sécurité

Pour votre sécurité :

- **Maximum 50 étapes** par plan (configurable)
- **Timeout de 30 minutes** par défaut
- **Validation requise** avant l'exécution
- **Arrêt possible** à tout moment (Ctrl+C)
- **Backup automatique** avant modification de fichiers

## Dépannage

### L'agent ne se lance pas

Vérifiez :
1. Ollama est bien lancé (`ollama serve`)
2. Un modèle est installé (`ollama list`)
3. Le mode agent est activé dans settings.py

### Le code généré n'est pas bon

- Utilisez un modèle plus performant (mistral, llama2:13b)
- Soyez plus précis dans votre demande
- Modifiez les prompts dans `config/code_prompts.py`

### L'exécution est trop lente

- Utilisez un modèle plus léger (phi, mistral:7b)
- Réduisez AGENT_PAUSE_STEPS dans .env
- Augmentez le timeout Ollama

## Astuces

### 💡 Soyez Précis

Au lieu de :
```
> crée une API
```

Préférez :
```
> crée une API REST avec FastAPI, authentification JWT,
  PostgreSQL et documentation Swagger
```

### 💡 Demandez des Features Spécifiques

```
> crée un bot Discord avec:
  - commandes de modération (ban, kick, mute)
  - système de niveaux et XP
  - logs des actions
  - base de données SQLite
```

### 💡 Combinez avec les Commandes Normales

Après avoir créé un projet :

```
> /agent crée un projet Flask

[Projet créé]

> va dans le dossier du projet
> installe les dépendances
> lance l'application
```

## Prochaines Fonctionnalités

- [ ] Modification du plan avant exécution
- [ ] Templates personnalisés
- [ ] Export/Import de plans
- [ ] Mode batch pour plusieurs projets
- [ ] Intégration avec des APIs externes
- [ ] Tests automatiques générés

---

🎉 **Profitez de votre Terminal IA Autonome!**

Pour toute question : tapez `/help` dans le terminal
