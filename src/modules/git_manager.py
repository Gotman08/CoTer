"""Gestionnaire Git pour automatiser les opérations de versioning"""

import subprocess
import os
from pathlib import Path
from typing import Dict, Optional, List

class GitManager:
    """Gère les opérations Git automatiquement"""

    def __init__(self, ollama_client=None, logger=None):
        """
        Initialise le gestionnaire Git

        Args:
            ollama_client: Client Ollama pour générer des messages de commit intelligents
            logger: Logger pour les messages
        """
        self.ollama = ollama_client
        self.logger = logger

    def init_repository(self, path: str) -> Dict:
        """
        Initialise un dépôt Git

        Args:
            path: Chemin du dossier à initialiser

        Returns:
            Dict avec résultat
        """
        try:
            if not os.path.exists(path):
                return {
                    'success': False,
                    'error': f'Chemin {path} introuvable'
                }

            # Vérifier si déjà un repo git
            git_dir = os.path.join(path, '.git')
            if os.path.exists(git_dir):
                return {
                    'success': True,
                    'message': 'Dépôt Git déjà initialisé',
                    'already_exists': True
                }

            # Initialiser git
            result = subprocess.run(
                ['git', 'init'],
                cwd=path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                if self.logger:
                    self.logger.info(f"Git initialisé dans {path}")

                # Créer .gitignore par défaut
                self._create_default_gitignore(path)

                return {
                    'success': True,
                    'message': 'Dépôt Git initialisé',
                    'path': path
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }

        except FileNotFoundError:
            return {
                'success': False,
                'error': 'Git n\'est pas installé sur ce système'
            }
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur init git: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def commit(self, path: str, message: Optional[str] = None, files: Optional[List[str]] = None) -> Dict:
        """
        Crée un commit

        Args:
            path: Chemin du dépôt
            message: Message de commit (généré automatiquement si None)
            files: Liste de fichiers à ajouter (tous si None)

        Returns:
            Dict avec résultat
        """
        try:
            # Vérifier que c'est un repo git
            if not os.path.exists(os.path.join(path, '.git')):
                return {
                    'success': False,
                    'error': 'Pas un dépôt Git'
                }

            # Ajouter les fichiers
            if files:
                for file in files:
                    result = subprocess.run(
                        ['git', 'add', file],
                        cwd=path,
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        if self.logger:
                            self.logger.warning(f"Erreur ajout {file}: {result.stderr}")
            else:
                # Ajouter tous les fichiers
                subprocess.run(
                    ['git', 'add', '.'],
                    cwd=path,
                    capture_output=True,
                    text=True
                )

            # Générer le message si non fourni
            if not message:
                message = self._generate_commit_message(path)

            # Créer le commit
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                if self.logger:
                    self.logger.info(f"Commit créé: {message}")
                return {
                    'success': True,
                    'message': message,
                    'output': result.stdout
                }
            elif 'nothing to commit' in result.stdout:
                return {
                    'success': True,
                    'message': 'Rien à committer',
                    'nothing_to_commit': True
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or result.stdout
                }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur commit: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_commit_message(self, path: str) -> str:
        """
        Génère un message de commit intelligent

        Args:
            path: Chemin du dépôt

        Returns:
            Message de commit
        """
        try:
            # Obtenir le statut git
            result = subprocess.run(
                ['git', 'status', '--short'],
                cwd=path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return "Update project files"

            status = result.stdout

            # Obtenir le diff
            diff_result = subprocess.run(
                ['git', 'diff', '--cached', '--stat'],
                cwd=path,
                capture_output=True,
                text=True
            )

            diff_stat = diff_result.stdout if diff_result.returncode == 0 else ""

            # Si Ollama disponible, générer un message intelligent
            if self.ollama:
                prompt = f"""Génère un message de commit git concis et descriptif basé sur ces changements:

STATUS:
{status}

STATS:
{diff_stat}

Règles:
- Message en français
- Maximum 50 caractères
- Commence par un verbe (Ajoute, Modifie, Corrige, Supprime, etc.)
- Décrit l'essentiel des changements

Exemples:
- "Ajoute module d'authentification JWT"
- "Corrige bug validation formulaire"
- "Modifie structure base de données"

Réponds UNIQUEMENT avec le message de commit, rien d'autre."""

                try:
                    message = self.ollama.generate(prompt, system_prompt="Tu es un expert Git. Génère UNIQUEMENT le message de commit, sans guillemets ni explications.")
                    message = message.strip().strip('"').strip("'")

                    # Limiter à 72 caractères
                    if len(message) > 72:
                        message = message[:69] + "..."

                    return message
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Erreur génération message: {e}")

            # Message par défaut basé sur le statut
            return self._generate_simple_commit_message(status)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur génération message: {e}")
            return "Update project files"

    def _generate_simple_commit_message(self, status: str) -> str:
        """
        Génère un message simple basé sur le statut

        Args:
            status: Sortie de git status --short

        Returns:
            Message de commit
        """
        lines = status.strip().split('\n')

        new_files = sum(1 for line in lines if line.startswith('A '))
        modified_files = sum(1 for line in lines if line.startswith('M '))
        deleted_files = sum(1 for line in lines if line.startswith('D '))

        if new_files > 0 and modified_files == 0 and deleted_files == 0:
            return f"Ajoute {new_files} nouveau{'x' if new_files > 1 else ''} fichier{'s' if new_files > 1 else ''}"
        elif modified_files > 0 and new_files == 0 and deleted_files == 0:
            return f"Modifie {modified_files} fichier{'s' if modified_files > 1 else ''}"
        elif deleted_files > 0 and new_files == 0 and modified_files == 0:
            return f"Supprime {deleted_files} fichier{'s' if deleted_files > 1 else ''}"
        else:
            return "Met à jour les fichiers du projet"

    def _create_default_gitignore(self, path: str):
        """
        Crée un .gitignore par défaut

        Args:
            path: Chemin du dépôt
        """
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db

# Project specific
*.bak
.pytest_cache/
node_modules/
dist/
build/
"""

        gitignore_path = os.path.join(path, '.gitignore')

        try:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
            if self.logger:
                self.logger.debug(f".gitignore créé: {gitignore_path}")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Erreur création .gitignore: {e}")

    def get_status(self, path: str) -> Dict:
        """
        Récupère le statut Git

        Args:
            path: Chemin du dépôt

        Returns:
            Dict avec statut
        """
        try:
            result = subprocess.run(
                ['git', 'status', '--short'],
                cwd=path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return {
                    'success': True,
                    'status': result.stdout,
                    'has_changes': bool(result.stdout.strip())
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def push(self, path: str, remote: str = 'origin', branch: str = 'main') -> Dict:
        """
        Push vers un remote

        Args:
            path: Chemin du dépôt
            remote: Nom du remote
            branch: Branche à pusher

        Returns:
            Dict avec résultat
        """
        try:
            result = subprocess.run(
                ['git', 'push', remote, branch],
                cwd=path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                if self.logger:
                    self.logger.info(f"Push réussi vers {remote}/{branch}")
                return {
                    'success': True,
                    'message': f'Push réussi vers {remote}/{branch}'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur push: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def is_git_repo(self, path: str) -> bool:
        """
        Vérifie si un chemin est un dépôt Git

        Args:
            path: Chemin à vérifier

        Returns:
            True si c'est un dépôt Git
        """
        return os.path.exists(os.path.join(path, '.git'))
