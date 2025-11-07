"""
Parser générique pour extraire les balises de la réponse IA.

Permet de structurer la réponse de l'IA avec des balises comme:
[Title Commande], [Description], [Commande], [DANGER], etc.
"""

import re
from typing import Dict, List, Optional, Tuple


class TagParser:
    """Parser générique pour extraire les sections balisées d'un texte"""

    # Balises connues et supportées
    KNOWN_TAGS = [
        'Title Commande',
        'Description',
        'Commande',
        'no Commande',
        'DANGER',
        'Titre Code',
        'Code',
        'fichier',
        'NO_COMMAND',  # Alias pour rétrocompatibilité
    ]

    def __init__(self):
        """Initialise le parser de balises"""
        # Créer le pattern regex pour détecter toutes les balises
        # Pattern: [balise] (case-insensitive pour certaines)
        tags_pattern = '|'.join(re.escape(tag) for tag in self.KNOWN_TAGS)
        self.tag_regex = re.compile(rf'\[({tags_pattern})\]', re.IGNORECASE)

    def parse(self, text: str) -> Dict[str, List[str]]:
        """
        Parse le texte et extrait toutes les sections balisées.

        Args:
            text: Texte contenant des balises [Tag]

        Returns:
            Dictionnaire {tag_name: [content1, content2, ...]}
            Si une balise apparaît plusieurs fois, tous les contenus sont dans la liste.

        Exemple:
            Input: "[Title] Bonjour [Description] Test [Title] Autre"
            Output: {'Title': ['Bonjour', 'Autre'], 'Description': ['Test']}
        """
        if not text or not text.strip():
            return {}

        # Trouver toutes les balises avec leurs positions
        matches = list(self.tag_regex.finditer(text))

        if not matches:
            # Pas de balises trouvées - retourner le texte brut comme "raw"
            return {'raw': [text.strip()]}

        # Extraire les sections entre les balises
        sections: Dict[str, List[str]] = {}

        for i, match in enumerate(matches):
            tag_name = match.group(1)  # Nom de la balise (sans les crochets)
            start_pos = match.end()    # Position après la balise

            # Fin de la section = début de la prochaine balise ou fin du texte
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            # Extraire le contenu de cette section
            content = text[start_pos:end_pos].strip()

            # Normaliser le nom de la balise (capitalisation)
            tag_name_normalized = self._normalize_tag_name(tag_name)

            # Ajouter à la liste des contenus pour cette balise
            if tag_name_normalized not in sections:
                sections[tag_name_normalized] = []
            sections[tag_name_normalized].append(content)

        return sections

    def _normalize_tag_name(self, tag: str) -> str:
        """
        Normalise le nom d'une balise pour cohérence.

        Args:
            tag: Nom de balise brut (peut avoir différentes capitalisations)

        Returns:
            Nom normalisé de la balise
        """
        # Cas spécial : DANGER et NO_COMMAND doivent rester en majuscules
        if tag.upper() in ['DANGER', 'NO_COMMAND']:
            return tag.upper()

        # Pour les autres, chercher la version canonique dans KNOWN_TAGS
        for known_tag in self.KNOWN_TAGS:
            if tag.lower() == known_tag.lower():
                return known_tag

        # Si inconnue, retourner telle quelle
        return tag

    def extract_command(self, parsed: Dict[str, List[str]]) -> Optional[str]:
        """
        Extrait la commande depuis les sections parsées.

        Cherche dans l'ordre de priorité :
        1. [Commande]
        2. [DANGER] (commande dangereuse)

        Args:
            parsed: Résultat de parse()

        Returns:
            La commande trouvée ou None
        """
        # 1. Chercher [Commande]
        if 'Commande' in parsed and parsed['Commande']:
            return parsed['Commande'][0].strip()

        # 2. Chercher [DANGER]
        if 'DANGER' in parsed and parsed['DANGER']:
            return parsed['DANGER'][0].strip()

        return None

    def has_tag(self, parsed: Dict[str, List[str]], tag_name: str) -> bool:
        """
        Vérifie si une balise spécifique est présente.

        Args:
            parsed: Résultat de parse()
            tag_name: Nom de la balise à chercher

        Returns:
            True si la balise existe et a du contenu
        """
        normalized_tag = self._normalize_tag_name(tag_name)
        return normalized_tag in parsed and len(parsed[normalized_tag]) > 0

    def get_tag_content(self, parsed: Dict[str, List[str]], tag_name: str) -> Optional[str]:
        """
        Récupère le contenu de la première occurrence d'une balise.

        Args:
            parsed: Résultat de parse()
            tag_name: Nom de la balise

        Returns:
            Contenu de la balise ou None si pas trouvée
        """
        normalized_tag = self._normalize_tag_name(tag_name)
        if normalized_tag in parsed and parsed[normalized_tag]:
            return parsed[normalized_tag][0]
        return None

    def detect_tag_boundaries(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Détecte les positions de toutes les balises dans le texte.
        Utile pour le streaming token par token.

        Args:
            text: Texte à analyser

        Returns:
            Liste de tuples (tag_name, start_pos, end_pos)
        """
        matches = self.tag_regex.finditer(text)
        return [(match.group(1), match.start(), match.end()) for match in matches]

    @classmethod
    def is_known_tag(cls, tag_name: str) -> bool:
        """
        Vérifie si une balise est dans la liste des balises connues.

        Args:
            tag_name: Nom de balise à vérifier

        Returns:
            True si la balise est connue
        """
        return any(tag_name.lower() == known.lower() for known in cls.KNOWN_TAGS)


# ═══════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = ['TagParser']
