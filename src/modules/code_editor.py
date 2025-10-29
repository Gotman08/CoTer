"""Éditeur de code intelligent utilisant Ollama"""

import os
from pathlib import Path
from typing import Dict, Optional, List
import re

class CodeEditor:
    """Génère et édite des fichiers de code intelligemment"""

    def __init__(self, ollama_client, logger=None):
        """
        Initialise l'éditeur de code

        Args:
            ollama_client: Client Ollama pour génération
            logger: Logger pour les messages
        """
        self.ollama = ollama_client
        self.logger = logger

        # Extensions supportées et leurs types
        self.language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'react',
            '.tsx': 'react-typescript',
            '.html': 'html',
            '.css': 'css',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.sql': 'sql',
            '.sh': 'bash',
            '.md': 'markdown',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.txt': 'text'
        }

    def create_file(self, file_path: str, description: str, context: Dict = None) -> Dict:
        """
        Crée un fichier avec du code généré

        Args:
            file_path: Chemin du fichier à créer
            description: Description de ce que doit faire le fichier
            context: Contexte additionnel (projet, dépendances, etc.)

        Returns:
            Dict avec 'success', 'file_path', 'lines_written'
        """
        try:
            # Déterminer le langage
            ext = Path(file_path).suffix
            language = self.language_map.get(ext, 'text')

            if self.logger:
                self.logger.info(f"Génération de {file_path} ({language})")

            # Générer le contenu
            content = self._generate_file_content(
                file_path=file_path,
                description=description,
                language=language,
                context=context
            )

            # Créer les dossiers parents si nécessaire
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Écrire le fichier
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            lines_written = len(content.split('\n'))

            if self.logger:
                self.logger.info(f"Fichier créé: {file_path} ({lines_written} lignes)")

            return {
                'success': True,
                'file_path': file_path,
                'lines_written': lines_written,
                'message': f'Fichier créé avec succès'
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur création fichier {file_path}: {e}")
            return {
                'success': False,
                'file_path': file_path,
                'error': str(e)
            }

    def edit_file(self, file_path: str, modification_request: str) -> Dict:
        """
        Modifie un fichier existant intelligemment

        Args:
            file_path: Chemin du fichier à modifier
            modification_request: Description de la modification

        Returns:
            Dict avec résultat
        """
        try:
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': f'Fichier {file_path} introuvable'
                }

            # Lire le fichier actuel
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()

            # Backup
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(current_content)

            if self.logger:
                self.logger.info(f"Backup créé: {backup_path}")

            # Générer la modification
            new_content = self._generate_file_modification(
                file_path=file_path,
                current_content=current_content,
                modification_request=modification_request
            )

            # Écrire le nouveau contenu
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            if self.logger:
                self.logger.info(f"Fichier modifié: {file_path}")

            return {
                'success': True,
                'file_path': file_path,
                'backup_path': backup_path,
                'message': 'Fichier modifié avec succès'
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur modification {file_path}: {e}")
            return {
                'success': False,
                'file_path': file_path,
                'error': str(e)
            }

    def _generate_file_content(self, file_path: str, description: str, language: str, context: Dict = None) -> str:
        """
        Génère le contenu d'un fichier via Ollama

        Args:
            file_path: Chemin du fichier
            description: Description
            language: Langage de programmation
            context: Contexte du projet

        Returns:
            Contenu généré
        """
        # Construire le prompt
        prompt = self._build_generation_prompt(file_path, description, language, context)

        # Générer via Ollama
        response = self.ollama.generate(
            prompt,
            system_prompt=f"Tu es un expert en {language}. Génère du code propre, commenté et suivant les meilleures pratiques. Réponds UNIQUEMENT avec le code, sans explications ni balises markdown."
        )

        # Nettoyer la réponse
        content = self._clean_generated_code(response, language)

        return content

    def _build_generation_prompt(self, file_path: str, description: str, language: str, context: Dict = None) -> str:
        """Construit le prompt pour la génération"""
        context = context or {}

        filename = os.path.basename(file_path)
        project_name = context.get('project_name', 'mon_projet')
        dependencies = context.get('dependencies', [])
        project_type = context.get('project_type', '')

        prompt = f"""Génère le code complet pour ce fichier:

Fichier: {filename}
Langage: {language}
Description: {description}
Projet: {project_name}"""

        if project_type:
            prompt += f"\nType de projet: {project_type}"

        if dependencies:
            prompt += f"\nDépendances disponibles: {', '.join(dependencies)}"

        # Ajouter des instructions spécifiques selon le type de fichier
        if filename == 'main.py':
            prompt += "\n\nCe fichier est le point d'entrée principal. Inclus une structure claire avec if __name__ == '__main__'."

        elif filename == 'README.md':
            prompt += f"\n\nGénère un README complet avec: description, installation, utilisation, exemples."

        elif filename == 'requirements.txt':
            prompt += f"\n\nListe les dépendances Python nécessaires, une par ligne."

        elif filename.endswith('.html'):
            prompt += "\n\nGénère du HTML5 valide avec une structure sémantique."

        elif filename == '.env.example':
            prompt += "\n\nCrée un fichier d'exemple de variables d'environnement avec des commentaires."

        prompt += "\n\nGénère le code COMPLET et FONCTIONNEL. Ne mets PAS de balises markdown (```), juste le code pur."

        return prompt

    def _generate_file_modification(self, file_path: str, current_content: str, modification_request: str) -> str:
        """
        Génère une version modifiée d'un fichier

        Args:
            file_path: Chemin du fichier
            current_content: Contenu actuel
            modification_request: Demande de modification

        Returns:
            Nouveau contenu
        """
        ext = Path(file_path).suffix
        language = self.language_map.get(ext, 'text')

        prompt = f"""Modifie ce code selon la demande:

Fichier: {os.path.basename(file_path)}
Langage: {language}

CONTENU ACTUEL:
{current_content}

MODIFICATION DEMANDÉE:
{modification_request}

Génère le code COMPLET modifié. Garde tout ce qui n'est pas concerné par la modification.
Ne mets PAS de balises markdown, juste le code complet."""

        response = self.ollama.generate(
            prompt,
            system_prompt=f"Tu es un expert en {language}. Modifie le code avec précision en gardant le style et les conventions existantes. Réponds UNIQUEMENT avec le code complet modifié."
        )

        return self._clean_generated_code(response, language)

    def _clean_generated_code(self, response: str, language: str) -> str:
        """
        Nettoie le code généré par l'IA

        Args:
            response: Réponse brute de l'IA
            language: Langage du code

        Returns:
            Code nettoyé
        """
        # Enlever les balises markdown si présentes
        if '```' in response:
            # Extraire le code entre les balises
            pattern = r'```(?:' + language + r'|[a-z]*)\n(.*?)```'
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                response = matches[0]
            else:
                # Essayer sans spécifier le langage
                pattern = r'```(.*?)```'
                matches = re.findall(pattern, response, re.DOTALL)
                if matches:
                    response = matches[0]

        # Enlever les lignes d'explication avant/après le code
        lines = response.split('\n')
        code_lines = []
        in_code = False

        for line in lines:
            # Détecter le début du code
            if not in_code and (
                line.strip().startswith(('#', '//', '/*', '<!', '<', 'import', 'from', 'def ', 'class ', 'function', 'const ', 'let ', 'var '))
                or (language == 'python' and line and not line[0].isalpha())
            ):
                in_code = True

            if in_code:
                code_lines.append(line)

        result = '\n'.join(code_lines) if code_lines else response

        return result.strip() + '\n'

    def create_directory_structure(self, base_path: str, structure: List[Dict]) -> Dict:
        """
        Crée une structure de dossiers

        Args:
            base_path: Chemin de base
            structure: Liste de dicts avec 'type' et 'path'

        Returns:
            Résultat de la création
        """
        created = []
        errors = []

        try:
            for item in structure:
                if item.get('type') == 'dir':
                    dir_path = os.path.join(base_path, item['path'])
                    try:
                        Path(dir_path).mkdir(parents=True, exist_ok=True)
                        created.append(dir_path)
                        if self.logger:
                            self.logger.debug(f"Dossier créé: {dir_path}")
                    except Exception as e:
                        errors.append({'path': dir_path, 'error': str(e)})

            return {
                'success': len(errors) == 0,
                'created': created,
                'errors': errors
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur création structure: {e}")
            return {
                'success': False,
                'created': created,
                'errors': [{'error': str(e)}]
            }

    def get_file_info(self, file_path: str) -> Dict:
        """
        Récupère des infos sur un fichier

        Args:
            file_path: Chemin du fichier

        Returns:
            Dict avec infos
        """
        try:
            if not os.path.exists(file_path):
                return {'exists': False}

            stat = os.stat(file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = len(content.split('\n'))

            ext = Path(file_path).suffix
            language = self.language_map.get(ext, 'unknown')

            return {
                'exists': True,
                'size': stat.st_size,
                'lines': lines,
                'language': language,
                'extension': ext
            }

        except Exception as e:
            return {
                'exists': True,
                'error': str(e)
            }
