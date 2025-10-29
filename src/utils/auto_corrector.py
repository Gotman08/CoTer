"""Module d'auto-correction pour détecter et corriger les erreurs automatiquement"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from config import constants

class AutoCorrector:
    """Analyse les erreurs et propose des corrections automatiques"""

    # Patterns d'erreurs courants (utilisation des constantes)
    ERROR_PATTERNS = {
        constants.ERROR_TYPES['COMMAND_NOT_FOUND']: [
            r'command not found',
            r'n\'est pas reconnu',
            r'not recognized',
            r'no such file or directory',
        ],
        constants.ERROR_TYPES['PERMISSION_DENIED']: [
            r'permission denied',
            r'access denied',
            r'operation not permitted',
            r'accès refusé',
        ],
        constants.ERROR_TYPES['SYNTAX_ERROR']: [
            r'syntax error',
            r'invalid syntax',
            r'unexpected token',
            r'erreur de syntaxe',
        ],
        constants.ERROR_TYPES['MODULE_NOT_FOUND']: [
            r'ModuleNotFoundError',
            r'ImportError',
            r'no module named',
            r'cannot import',
        ],
        constants.ERROR_TYPES['FILE_NOT_FOUND']: [
            r'FileNotFoundError',
            r'no such file',
            r'file not found',
            r'fichier introuvable',
        ],
        constants.ERROR_TYPES['CONNECTION_ERROR']: [
            r'connection refused',
            r'network unreachable',
            r'timeout',
            r'connection error',
        ],
        constants.ERROR_TYPES['DEPENDENCY_ERROR']: [
            r'missing dependency',
            r'package not found',
            r'could not find package',
        ],
        constants.ERROR_TYPES['PORT_IN_USE']: [
            r'address already in use',
            r'port.*already in use',
            r'bind: address already in use',
        ]
    }

    # Corrections automatiques connues
    AUTO_CORRECTIONS = {
        # Commandes mal orthographiées
        'pyhton': 'python',
        'pytohn': 'python',
        'pyton': 'python',
        'node.js': 'node',
        'nodejs': 'node',
        'gti': 'git',
        'clare': 'clear',
        'claer': 'clear',
        'cd..': 'cd ..',
        'sl': 'ls',
        'les': 'less',
        'grpe': 'grep',
        'gerp': 'grep',
        'maek': 'make',
        'mkae': 'make',
    }

    # Suggestions de corrections par type d'erreur
    CORRECTION_SUGGESTIONS = {
        'command_not_found': [
            'Vérifier l\'orthographe de la commande',
            'Vérifier que le package est installé',
            'Ajouter le chemin complet vers la commande',
            'Installer le package manquant',
        ],
        'permission_denied': [
            'Utiliser sudo pour les privilèges administrateur',
            'Vérifier les permissions du fichier (chmod)',
            'Changer le propriétaire du fichier (chown)',
        ],
        'module_not_found': [
            'Installer le module Python: pip install <module>',
            'Vérifier le nom du module',
            'Activer l\'environnement virtuel',
        ],
        'file_not_found': [
            'Vérifier le chemin du fichier',
            'Créer le fichier s\'il n\'existe pas',
            'Vérifier l\'orthographe du nom de fichier',
        ],
        'connection_error': [
            'Vérifier la connexion réseau',
            'Vérifier que le service est démarré',
            'Vérifier le firewall',
        ],
        'port_in_use': [
            'Changer le port utilisé',
            'Arrêter le processus qui utilise le port',
            'Utiliser lsof ou netstat pour identifier le processus',
        ]
    }

    def __init__(self, ollama_client=None, logger=None):
        """
        Initialise l'auto-correcteur

        Args:
            ollama_client: Client Ollama pour analyse IA
            logger: Logger pour les messages
        """
        self.ollama = ollama_client
        self.logger = logger

        # Historique des corrections
        self.correction_history = []
        self.max_history = constants.MAX_CORRECTION_HISTORY

    def analyze_error(self, command: str, error_output: str, exit_code: int) -> Dict[str, Any]:
        """
        Analyse une erreur et propose des corrections

        Args:
            command: Commande qui a échoué
            error_output: Message d'erreur
            exit_code: Code de sortie

        Returns:
            Dict avec l'analyse et les corrections proposées
        """
        error_lower = error_output.lower()

        # Identifier le type d'erreur
        error_type = self._identify_error_type(error_output)

        # Extraire les détails de l'erreur
        error_details = self._extract_error_details(command, error_output, error_type)

        # Proposer des corrections automatiques
        auto_fix = self._propose_auto_fix(command, error_output, error_type, error_details)

        # Proposer des corrections manuelles
        suggestions = self.CORRECTION_SUGGESTIONS.get(error_type, [])

        # Calculer un score de confiance pour la correction automatique
        confidence = self._calculate_confidence(error_type, auto_fix)

        analysis = {
            'error_type': error_type,
            'error_details': error_details,
            'original_command': command,
            'exit_code': exit_code,
            'auto_fix': auto_fix,
            'confidence': confidence,
            'suggestions': suggestions,
            'can_retry': auto_fix is not None and confidence > 0.6,
            'timestamp': datetime.now().isoformat()
        }

        # Ajouter à l'historique
        self._add_to_history(analysis)

        if self.logger:
            self.logger.info(f"Erreur analysée: {error_type}, confiance: {confidence}")

        return analysis

    def _identify_error_type(self, error_output: str) -> str:
        """
        Identifie le type d'erreur à partir du message

        Args:
            error_output: Message d'erreur

        Returns:
            Type d'erreur identifié
        """
        error_lower = error_output.lower()

        for error_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_lower, re.IGNORECASE):
                    return error_type

        return 'unknown'

    def _extract_error_details(self, command: str, error_output: str, error_type: str) -> Dict[str, Any]:
        """
        Extrait les détails spécifiques de l'erreur

        Args:
            command: Commande exécutée
            error_output: Message d'erreur
            error_type: Type d'erreur identifié

        Returns:
            Dict avec les détails
        """
        details = {}

        # Extraire le nom de la commande qui a échoué
        cmd_parts = command.split()
        if cmd_parts:
            details['command_name'] = cmd_parts[0]
            details['command_args'] = cmd_parts[1:] if len(cmd_parts) > 1 else []

        # Extraire des informations spécifiques selon le type d'erreur
        if error_type == 'command_not_found':
            # Essayer d'extraire le nom de la commande du message d'erreur
            match = re.search(r'command not found:\s*(\w+)', error_output, re.IGNORECASE)
            if match:
                details['missing_command'] = match.group(1)

        elif error_type == 'module_not_found':
            # Extraire le nom du module Python manquant
            match = re.search(r'no module named [\'"]?(\w+)', error_output, re.IGNORECASE)
            if match:
                details['missing_module'] = match.group(1)

        elif error_type == 'file_not_found':
            # Extraire le chemin du fichier manquant
            match = re.search(r'no such file or directory[:\s]+[\'"]?([^\'"]+)', error_output, re.IGNORECASE)
            if match:
                details['missing_file'] = match.group(1)

        elif error_type == 'port_in_use':
            # Extraire le numéro de port
            match = re.search(r'port\s+(\d+)', error_output, re.IGNORECASE)
            if match:
                details['port'] = match.group(1)

        return details

    def _propose_auto_fix(self, command: str, error_output: str,
                          error_type: str, error_details: Dict) -> Optional[str]:
        """
        Propose une correction automatique

        Args:
            command: Commande qui a échoué
            error_output: Message d'erreur
            error_type: Type d'erreur
            error_details: Détails de l'erreur

        Returns:
            Commande corrigée ou None
        """
        cmd_parts = command.split()
        if not cmd_parts:
            return None

        cmd_name = cmd_parts[0]
        cmd_args = ' '.join(cmd_parts[1:]) if len(cmd_parts) > 1 else ''

        # Correction orthographique automatique
        if cmd_name in self.AUTO_CORRECTIONS:
            corrected_cmd = self.AUTO_CORRECTIONS[cmd_name]
            return f"{corrected_cmd} {cmd_args}".strip()

        # Corrections spécifiques par type d'erreur
        if error_type == 'permission_denied':
            # Ajouter sudo si pas déjà présent
            if not command.startswith('sudo'):
                return f"sudo {command}"

        elif error_type == 'module_not_found':
            # Proposer d'installer le module Python
            if 'missing_module' in error_details:
                module = error_details['missing_module']
                return f"pip install {module}"

        elif error_type == 'command_not_found':
            # Vérifier si c'est une faute de frappe courante
            if cmd_name in self.AUTO_CORRECTIONS:
                return f"{self.AUTO_CORRECTIONS[cmd_name]} {cmd_args}".strip()

            # Proposer des commandes similaires communes
            similar = self._find_similar_commands(cmd_name)
            if similar:
                return f"{similar[0]} {cmd_args}".strip()

        elif error_type == 'file_not_found':
            # Si c'est un script Python, vérifier l'extension
            if cmd_name == 'python' and cmd_args and not cmd_args.endswith('.py'):
                return f"python {cmd_args}.py"

        return None

    def _find_similar_commands(self, command: str) -> List[str]:
        """
        Trouve des commandes similaires (distance de Levenshtein simple)

        Args:
            command: Commande à corriger

        Returns:
            Liste de commandes similaires
        """
        common_commands = [
            'ls', 'cd', 'pwd', 'cat', 'grep', 'find', 'echo', 'mkdir', 'rmdir',
            'cp', 'mv', 'rm', 'touch', 'chmod', 'chown', 'ps', 'kill', 'top',
            'git', 'python', 'node', 'npm', 'pip', 'make', 'gcc', 'java'
        ]

        similar = []
        for common in common_commands:
            # Distance simple: nombre de caractères différents
            if len(command) == len(common):
                diff = sum(c1 != c2 for c1, c2 in zip(command, common))
                if diff <= 2:  # Maximum 2 caractères différents
                    similar.append(common)

        return similar

    def _calculate_confidence(self, error_type: str, auto_fix: Optional[str]) -> float:
        """
        Calcule un score de confiance pour la correction automatique

        Args:
            error_type: Type d'erreur
            auto_fix: Correction proposée

        Returns:
            Score de confiance entre 0 et 1
        """
        if auto_fix is None:
            return 0.0

        # Score de base selon le type d'erreur
        base_scores = {
            'command_not_found': 0.7,
            'permission_denied': 0.9,
            'module_not_found': 0.85,
            'file_not_found': 0.6,
            'syntax_error': 0.4,
            'connection_error': 0.3,
            'port_in_use': 0.5,
            'unknown': 0.2
        }

        return base_scores.get(error_type, 0.5)

    def analyze_with_ai(self, command: str, error_output: str, context: str = "") -> Dict[str, Any]:
        """
        Utilise l'IA Ollama pour une analyse plus approfondie

        Args:
            command: Commande qui a échoué
            error_output: Message d'erreur
            context: Contexte additionnel

        Returns:
            Dict avec l'analyse IA
        """
        if not self.ollama:
            return {
                'success': False,
                'error': 'Client Ollama non disponible'
            }

        prompt = f"""Analyse l'erreur suivante et propose une correction:

Commande exécutée: {command}
Erreur: {error_output}
{f'Contexte: {context}' if context else ''}

Fournis:
1. Type d'erreur (en un mot)
2. Explication simple
3. Commande corrigée (si possible)
4. Étapes pour résoudre le problème

Format ta réponse ainsi:
TYPE: <type>
EXPLICATION: <explication>
CORRECTION: <commande corrigée>
ÉTAPES: <liste des étapes>
"""

        try:
            response = self.ollama.generate(prompt, system_prompt="Tu es un expert en débogage de commandes shell.")

            # Parser la réponse
            parsed = self._parse_ai_response(response)

            return {
                'success': True,
                'ai_analysis': parsed,
                'raw_response': response
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur analyse IA: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _parse_ai_response(self, response: str) -> Dict[str, str]:
        """
        Parse la réponse structurée de l'IA

        Args:
            response: Réponse de l'IA

        Returns:
            Dict avec les éléments parsés
        """
        parsed = {}

        # Extraire TYPE
        match = re.search(r'TYPE:\s*(.+)', response, re.IGNORECASE)
        if match:
            parsed['type'] = match.group(1).strip()

        # Extraire EXPLICATION
        match = re.search(r'EXPLICATION:\s*(.+?)(?=CORRECTION:|ÉTAPES:|$)', response, re.IGNORECASE | re.DOTALL)
        if match:
            parsed['explanation'] = match.group(1).strip()

        # Extraire CORRECTION
        match = re.search(r'CORRECTION:\s*(.+?)(?=ÉTAPES:|$)', response, re.IGNORECASE | re.DOTALL)
        if match:
            parsed['correction'] = match.group(1).strip()

        # Extraire ÉTAPES
        match = re.search(r'ÉTAPES:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
        if match:
            parsed['steps'] = match.group(1).strip()

        return parsed

    def _add_to_history(self, analysis: Dict):
        """Ajoute une analyse à l'historique"""
        self.correction_history.append(analysis)

        # Limiter la taille de l'historique
        if len(self.correction_history) > self.max_history:
            self.correction_history.pop(0)

    def get_correction_stats(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur les corrections

        Returns:
            Dict avec les stats
        """
        if not self.correction_history:
            return {
                'total_errors': 0,
                'message': 'Aucune erreur analysée'
            }

        total = len(self.correction_history)

        # Compter par type
        error_types = {}
        auto_fixable = 0
        high_confidence = 0

        for analysis in self.correction_history:
            error_type = analysis.get('error_type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1

            if analysis.get('can_retry'):
                auto_fixable += 1

            if analysis.get('confidence', 0) > 0.7:
                high_confidence += 1

        return {
            'total_errors': total,
            'error_types': error_types,
            'auto_fixable': auto_fixable,
            'auto_fixable_percent': round((auto_fixable / total * 100), 1) if total > 0 else 0,
            'high_confidence': high_confidence,
            'high_confidence_percent': round((high_confidence / total * 100), 1) if total > 0 else 0
        }

    def get_last_error_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Retourne la dernière analyse d'erreur

        Returns:
            Dict avec l'analyse ou None
        """
        if not self.correction_history:
            return None

        return self.correction_history[-1]
