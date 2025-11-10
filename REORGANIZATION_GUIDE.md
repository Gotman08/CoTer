# Guide de Réorganisation du Projet CoTer

## 📋 Vue d'ensemble

Ce guide explique comment utiliser le script `reorganize_project.py` pour réorganiser automatiquement l'architecture du projet CoTer.

Le script effectue une restructuration complète en 2 phases:
- **Phase 1**: Nettoyage et renommages (correction des conflits)
- **Phase 2**: Restructuration des dossiers `src/modules/` et `src/utils/`

---

## 🎯 Objectifs de la Réorganisation

### Problèmes résolus:
1. ✅ Conflits de noms (`prompt_manager.py` dupliqué)
2. ✅ Fichiers backup dans le code source
3. ✅ Dossiers `modules/` et `utils/` trop encombrés (11 et 19 fichiers)
4. ✅ Architecture peu claire (responsabilités mélangées)

### Structure finale:
```
src/
├── core/                    (Inchangé)
├── modules/
│   ├── agent/              ← NOUVEAU (orchestration agent)
│   ├── planning/           ← NOUVEAU (planification)
│   ├── execution/          ← NOUVEAU (exécution commandes)
│   └── tools/              ← NOUVEAU (outils externes)
├── utils/
│   ├── optimization/       ← NOUVEAU (optimisations hardware)
│   ├── execution/          ← NOUVEAU (parallélisme)
│   ├── persistence/        ← NOUVEAU (cache, config, rollback)
│   ├── services/           ← NOUVEAU (services externes)
│   └── helpers/            ← NOUVEAU (utilitaires génériques)
├── terminal/               (Inchangé)
└── security/               (Inchangé)
```

---

## 🚀 Utilisation du Script

### Étape 1: Test en mode DRY-RUN (Simulation)

**Recommandé en premier!** Visualisez les changements sans modification réelle:

```bash
python reorganize_project.py --dry-run
```

**Ce que fait le dry-run:**
- ✅ Affiche tous les changements qui seraient effectués
- ✅ Vérifie que tous les fichiers existent
- ✅ Génère un log JSON des opérations prévues
- ❌ N'effectue AUCUNE modification réelle

**Sortie attendue:**
```
[10:30:15] 🔵 INFO: MODE DRY-RUN: Aucune modification ne sera effectuée
[10:30:15] 🔵 INFO: ========================================
[10:30:15] 🔵 INFO: PHASE 1: NETTOYAGE ET RENOMMAGES
[10:30:15] 🔵 INFO: Supprimé: src/modules/autonomous_agent.py.backup
[10:30:15] 🔵 INFO: Renommé: src/core/prompt_manager.py → src/core/shell_prompt_manager.py
...
```

---

### Étape 2: Exécution Réelle

**⚠️ IMPORTANT:** Un commit git a déjà été créé automatiquement avant de lancer cette étape.

```bash
python reorganize_project.py
```

**Ce que fait l'exécution:**
1. ✅ Crée un backup automatique dans `.backup_YYYYMMDD_HHMMSS/`
2. ✅ Effectue tous les déplacements de fichiers
3. ✅ Met à jour tous les imports automatiquement
4. ✅ Génère un log JSON détaillé

**Sortie attendue:**
```
[10:35:20] ✅ INFO: Création backup: .backup_20251110_103520
[10:35:21] ✅ INFO: Backup créé avec succès
[10:35:21] ✅ INFO: ========================================
[10:35:21] ✅ INFO: PHASE 1: NETTOYAGE ET RENOMMAGES
[10:35:21] ✅ INFO: Supprimé: src/modules/autonomous_agent.py.backup
...
[10:35:45] ✅ INFO: ✅ RÉORGANISATION TERMINÉE AVEC SUCCÈS
[10:35:45] ✅ INFO: Backup disponible dans: .backup_20251110_103520
```

---

### Étape 3: Vérification

Testez que l'application fonctionne toujours:

```bash
# Tester le lancement
python main.py

# Tester les imports
python -m pytest tests/ -v

# Vérifier qu'aucune erreur d'import n'apparaît
python -c "from src.terminal_interface import TerminalInterface; print('✅ Imports OK')"
```

**Si tout fonctionne:**
```bash
# Créer un commit avec les changements
git add .
git commit -m "refactor: Réorganisation complète de l'architecture du projet

- Restructuration de src/modules/ en 4 sous-dossiers
- Restructuration de src/utils/ en 5 sous-dossiers
- Résolution des conflits de noms (prompt_manager)
- Mise à jour automatique de tous les imports
"
```

---

### Étape 4: Rollback (si problème)

Si l'application ne fonctionne plus correctement, annulez les changements:

```bash
python reorganize_project.py --rollback
```

**Ce que fait le rollback:**
1. ✅ Trouve le backup le plus récent
2. ✅ Demande confirmation avant de continuer
3. ✅ Restaure tous les dossiers `src/`, `config/`, `tests/`
4. ✅ Conserve le backup pour référence

**Sortie attendue:**
```
[10:40:10] ✅ INFO: ROLLBACK: Recherche du dernier backup...
[10:40:10] ✅ INFO: Backup trouvé: .backup_20251110_103520

⚠️  ATTENTION: Cette action va restaurer le projet à son état précédent
Backup: .backup_20251110_103520
Continuer? (oui/non): oui

[10:40:15] ✅ INFO: Restauré: src/
[10:40:16] ✅ INFO: Restauré: config/
[10:40:16] ✅ INFO: Restauré: tests/
[10:40:16] ✅ INFO: ✅ ROLLBACK TERMINÉ
```

---

## 📊 Détails des Changements

### Phase 1: Nettoyage

| Action | Fichier | Résultat |
|--------|---------|----------|
| Suppression | `src/modules/autonomous_agent.py.backup` | ✅ Fichier backup supprimé |
| Renommage | `src/core/prompt_manager.py` | → `shell_prompt_manager.py` |
| Renommage | `src/terminal/prompt_manager.py` | → `terminal_prompt_manager.py` |
| Warning | `venv/` ou `.venv/` redondants | ⚠️ Suppression manuelle requise |

### Phase 2.1: Restructuration de `src/modules/`

**11 fichiers** réorganisés en **4 sous-dossiers:**

```
modules/
├── agent/                          (4 fichiers)
│   ├── autonomous_agent.py        ← orchestrateur principal
│   ├── agent_orchestrator.py      ← machine à états
│   ├── agent_facades.py           ← interfaces rollback/correction
│   └── step_executor.py           ← exécution d'étapes
│
├── planning/                       (3 fichiers)
│   ├── project_planner.py         ← planification projets
│   ├── background_planner.py      ← planification arrière-plan
│   └── plan_storage.py            ← persistance des plans
│
├── execution/                      (3 fichiers)
│   ├── command_executor.py        ← exécution commandes
│   ├── command_parser.py          ← parsing des commandes
│   └── code_editor.py             ← édition de fichiers
│
└── tools/                          (2 fichiers)
    ├── git_manager.py             ← gestion Git
    └── ollama_client.py           ← client Ollama IA
```

### Phase 2.2: Restructuration de `src/utils/`

**19 fichiers** réorganisés en **5 sous-dossiers:**

```
utils/
├── optimization/                   (3 fichiers)
│   ├── hardware.py                ← ex: hardware_optimizer.py
│   ├── arm.py                     ← ex: arm_optimizer.py
│   └── gc.py                      ← ex: gc_optimizer.py
│
├── execution/                      (3 fichiers)
│   ├── parallel_executor.py       ← exécution parallèle
│   ├── parallel_workers.py        ← pool de workers
│   └── command_helpers.py         ← helpers de commandes
│
├── persistence/                    (4 fichiers)
│   ├── cache_manager.py           ← gestion cache
│   ├── user_config.py             ← configuration utilisateur
│   ├── rollback_manager.py        ← gestion rollback
│   └── auto_corrector.py          ← auto-correction erreurs
│
├── services/                       (1 fichier)
│   └── ollama_manager.py          ← gestion service Ollama
│
└── helpers/                        (4 fichiers)
    ├── logger.py                  ← logging centralisé
    ├── tag_parser.py              ← parsing de tags
    ├── ui_helpers.py              ← helpers UI
    └── text_processing.py         ← traitement texte
```

---

## 📈 Impact Estimé

### Fichiers modifiés:
- **Phase 1**: ~30 fichiers (renommages + imports)
- **Phase 2**: ~100 fichiers (déplacements + imports)
- **Total**: ~130 fichiers

### Imports mis à jour:
Le script met automatiquement à jour tous les imports dans:
- ✅ `src/**/*.py` (code source)
- ✅ `config/**/*.py` (configuration)
- ✅ `tests/**/*.py` (tests)
- ✅ `*.py` (fichiers racine)

### Exemples d'imports mis à jour:

**Avant:**
```python
from src.modules.autonomous_agent import AutonomousAgent
from src.utils.hardware_optimizer import HardwareOptimizer
from src.core.prompt_manager import PromptManager
```

**Après:**
```python
from src.modules.agent.autonomous_agent import AutonomousAgent
from src.utils.optimization.hardware import HardwareOptimizer
from src.core.shell_prompt_manager import PromptManager
```

---

## ⚙️ Options du Script

### Ligne de commande:

```bash
# Simulation (recommandé en premier)
python reorganize_project.py --dry-run

# Exécution réelle
python reorganize_project.py

# Annuler les changements
python reorganize_project.py --rollback
```

### Fichiers générés:

1. **Backup automatique:** `.backup_YYYYMMDD_HHMMSS/`
   - Contient: `src/`, `config/`, `tests/`
   - Créé avant toute modification
   - Utilisé pour le rollback

2. **Log JSON:** `reorganization_log_YYYYMMDD_HHMMSS.json`
   - Liste toutes les opérations effectuées
   - Timestamp de chaque action
   - Utile pour audit/debugging

---

## 🔍 Troubleshooting

### Problème: "Fichier non trouvé"

**Cause:** Un fichier listé dans la réorganisation n'existe pas

**Solution:**
1. Vérifiez que vous êtes à la racine du projet CoTer
2. Vérifiez que le fichier n'a pas déjà été déplacé
3. Consultez le log JSON pour voir quels fichiers ont été traités

### Problème: "Erreur d'import après réorganisation"

**Cause:** Un import n'a pas été mis à jour correctement

**Solution:**
1. Vérifiez le fichier avec l'erreur
2. Cherchez l'ancien import: `git grep "from src.modules.autonomous_agent"`
3. Mettez à jour manuellement vers: `from src.modules.agent.autonomous_agent`

### Problème: "Le script plante en plein milieu"

**Cause:** Erreur inattendue (permissions, disque plein, etc.)

**Solution:**
```bash
# Rollback immédiat
python reorganize_project.py --rollback

# Vérifier l'erreur dans le log
cat reorganization_log_*.json

# Corriger le problème et relancer
```

---

## 📝 Notes Importantes

### ⚠️ Avant d'exécuter:
1. ✅ Assurez-vous qu'un commit git existe (déjà fait automatiquement)
2. ✅ Fermez tous les fichiers ouverts dans votre éditeur
3. ✅ Fermez l'application si elle est en cours d'exécution
4. ✅ Lancez d'abord en mode `--dry-run`

### ✅ Après exécution:
1. Testez l'application: `python main.py`
2. Lancez les tests: `pytest tests/`
3. Vérifiez les imports: cherchez les erreurs `ModuleNotFoundError`
4. Si OK: créez un commit git
5. Si KO: lancez le rollback

### 🎯 Compatibilité:
- ✅ Python 3.8+
- ✅ Windows, Linux, macOS
- ✅ WSL compatible

---

## 📞 Support

Si vous rencontrez des problèmes:

1. **Consultez le log JSON** généré pour voir exactement ce qui s'est passé
2. **Utilisez le rollback** pour revenir à l'état précédent
3. **Vérifiez les backups** dans `.backup_*/`
4. **Consultez les commits git** pour voir l'historique

---

## ✨ Avantages de la Nouvelle Structure

### Avant:
```
src/modules/  (11 fichiers en vrac)
src/utils/    (19 fichiers en vrac)
```

### Après:
```
src/modules/  (4 sous-dossiers thématiques)
src/utils/    (5 sous-dossiers thématiques)
```

### Bénéfices:
- 🎯 **Clarté**: Responsabilités évidentes
- 🔍 **Navigation**: Trouver un fichier = connaître sa responsabilité
- 📦 **Modularité**: Sous-dossiers indépendants
- 🧪 **Testabilité**: Tests organisés par module
- 📚 **Documentation**: Architecture auto-documentée
- 🚀 **Évolutivité**: Ajout de nouveaux modules simplifié

---

## 🎉 Résumé

Ce script automatise complètement la réorganisation du projet CoTer:
- ✅ **Sûr**: Backup automatique + rollback
- ✅ **Rapide**: Traitement de ~130 fichiers en quelques secondes
- ✅ **Intelligent**: Mise à jour automatique des imports
- ✅ **Transparent**: Logs détaillés de toutes les opérations
- ✅ **Testable**: Mode dry-run pour validation

**Prêt à réorganiser? Lancez:**
```bash
python reorganize_project.py --dry-run
```

---

**Généré avec Claude Code - 2025-11-10**
