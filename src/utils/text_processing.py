"""
Utilitaires de traitement de texte
Centralise les fonctions de nettoyage et formatage de texte
"""

import re
from typing import List


def strip_ansi_codes(text: str) -> str:
    """
    Supprime toutes les séquences d'échappement ANSI/VT100 d'une chaîne

    Exemples de séquences supprimées:
    - ^[[?2004h / ^[[?2004l  (Bracketed Paste Mode)
    - ^[[0m                  (Reset couleur)
    - ^[[31m                 (Couleur rouge)
    - ^[[1;32m               (Gras + vert)

    Args:
        text: Texte contenant potentiellement des séquences ANSI

    Returns:
        Texte nettoyé sans séquences ANSI

    Examples:
        >>> strip_ansi_codes("\\x1b[31mRouge\\x1b[0m")
        'Rouge'
        >>> strip_ansi_codes("Normal \\x1b[1;32mVert gras\\x1b[0m Normal")
        'Normal Vert gras Normal'
    """
    # Pattern regex pour capturer TOUTES les séquences ANSI
    # Format: ESC [ params letter
    ansi_escape = re.compile(r'\x1b\[[0-9;?]*[a-zA-Zhl]')

    # Supprimer aussi les caractères de contrôle non-imprimables
    # sauf newline \n, tab \t, carriage return \r
    control_chars = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

    # Nettoyer en deux passes
    text = ansi_escape.sub('', text)
    text = control_chars.sub('', text)

    return text


def clean_command_echo(output: str, command: str) -> str:
    """
    Nettoie l'output d'un shell en supprimant l'écho de la commande

    Lorsqu'une commande est envoyée à un shell interactif, bash/zsh
    echo la commande avant d'afficher le résultat. Cette fonction
    supprime cet écho pour obtenir seulement l'output réel.

    Args:
        output: Output brut du shell (contient l'écho)
        command: Commande qui a été exécutée

    Returns:
        Output nettoyé sans l'écho de la commande

    Examples:
        >>> clean_command_echo("ls -la\\ntotal 48\\ndrwxr-xr-x", "ls -la")
        'total 48\\ndrwxr-xr-x'
    """
    lines = output.split('\n')

    # Supprimer UNIQUEMENT la ligne d'écho de la commande
    # IMPORTANT: Utiliser == et non 'in' pour ne pas supprimer l'output par erreur
    if lines and lines[0].strip() == command.strip():
        lines = lines[1:]

    # Supprimer les lignes vides au début
    while lines and not lines[0].strip():
        lines.pop(0)

    # Supprimer les lignes vides à la fin
    while lines and not lines[-1].strip():
        lines.pop()

    return '\n'.join(lines)


def extract_exit_code_from_output(output: str) -> int:
    """
    Extrait l'exit code depuis l'output de 'echo $?'

    Args:
        output: Output brut de la commande 'echo $?'

    Returns:
        Exit code (0 si non trouvé)

    Examples:
        >>> extract_exit_code_from_output("echo $?\\n0\\n")
        0
        >>> extract_exit_code_from_output("127\\n")
        127
    """
    lines = [l.strip() for l in output.split('\n') if l.strip()]

    # Chercher le nombre (exit code) - éviter la ligne "echo $?"
    for line in lines:
        # Ignorer les lignes contenant la commande elle-même
        if 'echo' in line.lower() or '$?' in line:
            continue
        # Prendre le premier nombre trouvé
        if line.isdigit():
            return int(line)

    return 0  # Défaut: succès


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale

    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
        suffix: Suffixe à ajouter si tronqué (par défaut: "...")

    Returns:
        Texte tronqué

    Examples:
        >>> truncate_text("Un texte très long", 10)
        'Un texte ...'
        >>> truncate_text("Court", 10)
        'Court'
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_bytes(size_bytes: int) -> str:
    """
    Formate une taille en bytes en unités lisibles

    Args:
        size_bytes: Taille en bytes

    Returns:
        Taille formatée (ex: "4.1 GB")

    Examples:
        >>> format_bytes(1024)
        '1.0 KB'
        >>> format_bytes(1536)
        '1.5 KB'
        >>> format_bytes(1048576)
        '1.0 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
