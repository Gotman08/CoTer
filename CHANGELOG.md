# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

## [1.0.0] - 2025-10-29

### Ajouté
- 🎉 Version initiale du Terminal IA Autonome
- 🤖 Intégration avec Ollama pour le parsing de langage naturel
- 🛡️ Système de sécurité complet avec validation des commandes
- 📝 Historique et logs détaillés des commandes
- 🎨 Interface CLI avec ASCII art
- ⚙️ Exécuteur de commandes sécurisé
- 📦 Support pour Raspberry Pi 5 (ARM64)
- 🔒 Confirmation obligatoire pour les commandes dangereuses
- 📚 Documentation complète avec README
- 🧪 Tests basiques pour le module de sécurité
- 🚀 Scripts de démarrage pour Linux et Windows

### Modules
- `ollama_client.py` - Client pour l'API Ollama
- `command_parser.py` - Parsing des demandes en langage naturel
- `command_executor.py` - Exécution sécurisée des commandes shell
- `terminal_interface.py` - Interface CLI principale
- `logger.py` - Système de logging
- `security.py` - Validation de sécurité

### Fonctionnalités
- Commandes spéciales: `/help`, `/quit`, `/clear`, `/history`, `/models`, `/info`
- Détection automatique des commandes dangereuses
- Support des chemins relatifs et absolus
- Gestion du répertoire courant avec `cd`
- Logs détaillés par jour

### Sécurité
- Liste noire de commandes interdites
- Détection de patterns dangereux
- Protection des chemins système
- Limitation de la taille des outputs
- Validation avant exécution

## [Planifié] - À venir

### À ajouter
- [ ] Mode batch pour exécuter des scripts
- [ ] Support pour les variables d'environnement personnalisées
- [ ] Plugin system pour étendre les fonctionnalités
- [ ] Interface web optionnelle
- [ ] Support multi-langue
- [ ] Tests unitaires complets
- [ ] Intégration continue (CI/CD)
- [ ] Métriques et statistiques d'utilisation
