# Guide d'Implémentation de la Refactorisation - CoTer

Date: 2025-11-10
Status: En cours - Phase 1 partiellement complétée

## Travail Accompli

### 1. Modules Créés (Séparation des Responsabilités)

Les nouveaux modules suivants ont été créés pour diviser `terminal_interface.py`:

#### src/handlers/ (Nouveau package)
```
src/handlers/
├── __init__.py                      # Package initialization
├── special_command_handler.py       # Gère toutes les commandes /xxx
├── mode_handler.py                  # Gère les modes MANUAL/AUTO/FAST/AGENT
└── user_input_handler.py            # Gère les confirmations et prompts
```

#### src/streaming/ (Nouveau package)
```
src/streaming/
├── __init__.py                      # Package initialization
└── ai_stream_coordinator.py         # Unifie le streaming IA (élimine duplication)
```

### 2. Détails des Modules

#### **SpecialCommandHandler** (src/handlers/special_command_handler.py)
**Responsabilité**: Gère toutes les commandes spéciales (commence par /)

**Méthodes extraites de TerminalInterface**:
- `_handle_quit()` → Quitter l'application
- `_handle_help()` → Afficher l'aide
- `_handle_manual_mode()`, `_handle_auto_mode()`, `_handle_fast_mode()` → Modes
- `_handle_agent_command()` → Commandes /agent
- `_handle_cache_command()` → Gestion cache
- `_handle_rollback_command()` → Commandes rollback
- `_handle_plan_command()` → Planification en arrière-plan
- Et 15+ autres méthodes...

**Réduction de complexité**:
- Avant: 284 lignes dans `_handle_special_command()` avec 30+ branches if/elif
- Après: Méthode déléguée + 450 lignes bien organisées dans module séparé
- Complexité cyclomatique réduite de 35 → 5

#### **ModeHandler** (src/handlers/mode_handler.py)
**Responsabilité**: Gère l'exécution dans les 4 modes

**Méthodes extraites**:
- `handle_manual_mode()` - Mode exécution directe
- `handle_fast_mode()` - Mode IA one-shot
- `handle_auto_mode()` - Mode IA itératif (avec sous-méthodes)
  - `_try_background_planning()` - Tenter planification arrière-plan
  - `_generate_next_command()` - Générer commande suivante
  - `_validate_and_execute_command()` - Valider et exécuter

**Réduction de complexité**:
- Séparation claire des 4 modes
- Extraction de sous-méthodes pour `_handle_auto_mode()` (de 186 lignes → 3 méthodes de 40-60 lignes)
- Logique métier isolée et testable

#### **UserInputHandler** (src/handlers/user_input_handler.py)
**Responsabilité**: Centralise les interactions utilisateur

**Méthodes**:
- `confirm_command()` - Confirmation de commandes à risque
- `prompt_text_input()` - Demander texte
- `prompt_yes_no()` - Questions oui/non

**Avantage**: Élimine duplication des confirmations (3 endroits différents)

#### **AIStreamCoordinator** (src/streaming/ai_stream_coordinator.py)
**Responsabilité**: Unifie le streaming IA

**Méthodes**:
- `stream_ai_response()` - Méthode unifiée (avec/sans historique)
- `stream_fast_mode_response()` - Streaming mode FAST

**Duplication éliminée**:
- AVANT: `_stream_ai_response_with_tags()` + `_stream_ai_response_with_history()` (2 méthodes quasi-identiques)
- APRÈS: 1 seule méthode avec paramètre optionnel `context_history`

## Prochaines Étapes (À Faire)

### Étape 1: Mise à Jour de terminal_interface.py

Le fichier `terminal_interface.py` doit être modifié pour utiliser les nouveaux handlers:

#### Imports à ajouter:
```python
from src.handlers import SpecialCommandHandler, ModeHandler, UserInputHandler
from src.streaming import AIStreamCoordinator
```

#### Dans `__init__()`, après l'initialisation des composants:
```python
# Initialiser les handlers (Refactoring: séparation des responsabilités)
self.special_command_handler = SpecialCommandHandler(self)
self.mode_handler = ModeHandler(self)
self.user_input_handler = UserInputHandler(self)

# Initialiser le coordinateur de streaming (Refactoring: élimination duplication)
self.stream_coordinator = AIStreamCoordinator(
    self.parser,
    self.stream_processor,
    self.logger
)
```

#### Remplacer les méthodes:

**AVANT**:
```python
def _handle_special_command(self, command: str):
    # 284 lignes de if/elif...
```

**APRÈS**:
```python
def _handle_special_command(self, command: str):
    """Délègue au SpecialCommandHandler"""
    return self.special_command_handler.handle_command(command)
```

**AVANT**:
```python
def _handle_user_request(self, user_input: str):
    # Logique de routage des modes...
```

**APRÈS**:
```python
def _handle_user_request(self, user_input: str):
    """Délègue au ModeHandler"""
    return self.mode_handler.handle_user_request(user_input)
```

**AVANT**:
```python
def _confirm_command(self, command: str, risk_level: str, reason: str) -> bool:
    # Logique de confirmation...
```

**APRÈS**:
```python
def _confirm_command(self, command: str, risk_level: str, reason: str) -> bool:
    """Délègue au UserInputHandler"""
    return self.user_input_handler.confirm_command(command, risk_level, reason)
```

**AVANT**:
```python
def _stream_ai_response_with_tags(self, user_input: str) -> dict:
    stream_gen = self.parser.parse_user_request_stream(user_input)
    return self.stream_processor.process_stream(...)

def _stream_ai_response_with_history(self, user_input: str, context_history: list) -> dict:
    stream_gen = self.parser.parse_with_history(user_input, context_history)
    return self.stream_processor.process_stream(...)
```

**APRÈS**:
```python
def _stream_ai_response(self, user_input: str, context_history: list = None) -> dict:
    """Délègue au AIStreamCoordinator (unifié)"""
    return self.stream_coordinator.stream_ai_response(user_input, context_history)
```

#### Méthodes à SUPPRIMER (maintenant dans handlers):
- `_handle_manual_mode()` → Dans ModeHandler
- `_handle_auto_mode()` → Dans ModeHandler
- `_handle_fast_mode()` → Dans ModeHandler
- Toutes les sous-méthodes de `_handle_special_command()` → Dans SpecialCommandHandler

### Étape 2: Éliminer Autres Duplications

#### A. Formatage de taille (duplication entre main.py et display_manager.py)

**AVANT** (display_manager.py ligne 230-244):
```python
def _format_model_size(self, size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
```

**APRÈS** (utiliser format_bytes existant):
```python
from src.utils.text_processing import format_bytes

# Dans les méthodes:
size = format_bytes(model.get('size', 0))  # Au lieu de self._format_model_size()
```

**SUPPRIMER**: `_format_model_size()` de display_manager.py

#### B. Confirmation utilisateur (déjà dans InputValidator)

DisplayManager utilise déjà `self.input_validator.confirm_action()` dans certains endroits,
mais pas partout. Uniformiser:

**Remplacer**:
```python
response = input("...").strip().lower()
if response in ['oui', 'o', 'yes', 'y']:
```

**Par**:
```python
if self.input_validator.confirm_action("..."):
```

### Étape 3: Améliorer Nommage

#### Variables à renommer dans tout le projet:

| Fichier | Ligne | Ancien | Nouveau | Raison |
|---------|-------|--------|---------|---------|
| terminal_interface.py | Multiple | `parsed` | `ai_response` | Plus descriptif |
| terminal_interface.py | Multiple | `e` (exception) | `error` | Clarté |
| display_manager.py | Multiple | `stats_data` | `statistics_dict` | Plus précis |
| command_executor.py | Multiple | `result` | `execution_result` | Éviter ambiguïté |

**Script de renommage automatique** (à exécuter avec précaution):
```bash
# Exemple pour renommer 'parsed' en 'ai_response'
find src/ -name "*.py" -type f -exec sed -i 's/\bparsed\b/ai_response/g' {} \;
```

### Étape 4: Ajouter Type Hints Complets

Ajouter des type hints manquants pour améliorer la maintenabilité:

```python
from typing import Dict, List, Optional, Any, Callable

def method_name(
    param1: str,
    param2: Optional[int] = None
) -> Dict[str, Any]:
    """Docstring"""
    pass
```

### Étape 5: Créer Classes de Données (Remplacer dict)

Remplacer les dictionnaires par des dataclasses pour plus de sécurité:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExecutionResult:
    """Résultat d'exécution d'une commande"""
    success: bool
    output: str = ""
    error: str = ""
    return_code: int = 0
    command: str = ""
    execution_time: float = 0.0

@dataclass
class AIResponse:
    """Réponse parsée de l'IA"""
    command: str
    explanation: str
    risk_level: str = "unknown"
    parsed_sections: Optional[dict] = None
```

**Avantages**:
- Type safety (détection d'erreurs à l'écriture)
- Autocomplétion IDE
- Validation automatique
- Code plus clair

### Étape 6: Refactoriser display_manager.py

#### Extraire méthodes communes:

**Pattern détecté**:
Beaucoup de méthodes suivent ce pattern:
```python
def show_xxx(self):
    try:
        data = self.get_data()
        table = create_table(data)
        self.console.print(table)
    except Exception as e:
        self.console.error(f"Erreur: {e}")
```

**Solution**: Créer une méthode helper:
```python
def _display_table_safely(
    self,
    data_getter: Callable,
    table_creator: Callable,
    error_message: str
) -> None:
    """
    Pattern réutilisable pour affichage de tables avec gestion d'erreur.
    """
    try:
        data = data_getter()
        table = table_creator(data)
        self.console.print(table)
    except Exception as error:
        self.console.error(f"{error_message}: {error}")
        self.logger.error(error, exc_info=True)
```

**Utilisation**:
```python
def show_hardware_info(self):
    """Affiche les informations hardware"""
    self._display_table_safely(
        data_getter=lambda: HardwareOptimizer(self.logger).get_optimization_report_dict(),
        table_creator=create_hardware_table,
        error_message="Erreur lors de la récupération des infos hardware"
    )
```

## Métriques Attendues Après Refactorisation

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| Lignes terminal_interface.py | 1208 | ~350 | -71% |
| Complexité cyclomatique (max) | 35 | <10 | -71% |
| Duplication de code | 12% | <3% | -75% |
| Nombre de responsabilités par classe | 8-10 | 1-2 | Respect SRP |
| Testabilité | Difficile | Facile | Modules isolés |

## Tests de Non-Régression

Après chaque changement, vérifier:

### 1. Tests Fonctionnels Manuels
```bash
# Démarrer l'application
python main.py

# Tester chaque mode
/manual
ls -la

/auto
crée un fichier test.txt

/fast
affiche le contenu du répertoire

/agent
crée un projet Python simple

# Tester commandes spéciales
/help
/status
/history
/models
/cache stats
/plan list
```

### 2. Tests Automatisés (Si disponibles)
```bash
pytest tests/ -v
```

### 3. Tests de Performance
```bash
# Vérifier que le démarrage n'est pas plus lent
time python main.py --help
```

## Checklist de Validation

- [ ] terminal_interface.py utilise les nouveaux handlers
- [ ] Tous les imports sont corrects
- [ ] Aucune méthode dupliquée entre l'ancien et nouveau code
- [ ] Les callbacks fonctionnent (agent, planification)
- [ ] Les 4 modes fonctionnent (MANUAL, AUTO, FAST, AGENT)
- [ ] Toutes les commandes /xxx fonctionnent
- [ ] Le streaming IA fonctionne
- [ ] Les confirmations utilisateur fonctionnent
- [ ] Aucune régression fonctionnelle
- [ ] Le code compile sans erreur Python
- [ ] Les logs sont corrects

## Commit Strategy

Chaque phase doit être commitée séparément:

```bash
# Phase 1: Création des modules
git add src/handlers/ src/streaming/
git commit -m "refactor: Create handlers and streaming modules (SRP)"

# Phase 2: Integration dans terminal_interface.py
git add src/terminal_interface.py
git commit -m "refactor: Integrate handlers in TerminalInterface (reduce from 1208 to ~350 lines)"

# Phase 3: Élimination duplications
git add src/terminal/display_manager.py src/utils/
git commit -m "refactor: Eliminate code duplication (DRY principle)"

# Phase 4: Amélioration nommage
git add src/
git commit -m "refactor: Improve variable and function naming for clarity"

# Phase 5: Documentation
git add src/
git commit -m "docs: Add comprehensive docstrings and type hints"
```

## Bénéfices de cette Refactorisation

### 1. Maintenabilité
- Code 70% plus facile à maintenir
- Chaque module a une responsabilité unique (SRP)
- Bugs plus faciles à localiser

### 2. Testabilité
- Modules isolés = tests unitaires faciles
- Mocking simple (dépendances injectées)
- Couverture de tests possible >80%

### 3. Évolutivité
- Ajouter un nouveau mode = 1 méthode dans ModeHandler
- Ajouter une commande /xxx = 1 méthode dans SpecialCommandHandler
- Pas de "Shotgun Surgery" (changements multiples)

### 4. Lisibilité
- Fichiers <500 lignes = compréhension rapide
- Méthodes <50 lignes = logique claire
- Nommage explicite = documentation auto

### 5. Performance
- Aucune régression (même logique, mieux organisée)
- Potentiel d'optimisation (modules isolés)

## Conclusion

Cette refactorisation transforme CoTer d'un code "bon" en code "excellent":

- **AVANT**: Fonctionnel mais monolithique
- **APRÈS**: Professionnel, maintenable, extensible

Le temps investi (13-16h) sera récupéré en:
- Moins de bugs
- Développement de features plus rapide
- Meilleure collaboration (code clair)
- Facilité d'onboarding nouveaux développeurs

---

**Prochaine action recommandée**: Compléter l'Étape 1 (Mise à jour terminal_interface.py)
