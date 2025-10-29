"""Workers standalone pour multiprocessing (fonctions picklable au top-level)"""

import os
import subprocess
import json
from typing import Dict, Any
from pathlib import Path


def execute_create_file_worker(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker pour créer un fichier (picklable, top-level function)

    Args:
        task_data: Dict contenant file_path, content, description

    Returns:
        Dict avec le résultat
    """
    try:
        file_path = task_data.get('file_path')
        content = task_data.get('content')

        if not file_path:
            return {
                'success': False,
                'error': 'file_path manquant'
            }

        # Créer les dossiers parents si nécessaire
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Écrire le fichier
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content or '')

        lines_written = len(content.split('\n')) if content else 0

        return {
            'success': True,
            'file_path': file_path,
            'lines_written': lines_written
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'file_path': task_data.get('file_path', 'unknown')
        }


def execute_run_command_worker(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker pour exécuter une commande shell (picklable, top-level function)

    Args:
        task_data: Dict contenant command, cwd, timeout

    Returns:
        Dict avec le résultat
    """
    try:
        command = task_data.get('command')
        cwd = task_data.get('cwd', '.')
        timeout = task_data.get('timeout', 120)

        if not command:
            return {
                'success': False,
                'error': 'Commande vide'
            }

        # Exécuter la commande
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else '',
            'exit_code': result.returncode,
            'command': command
        }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': f'Timeout après {timeout}s',
            'command': task_data.get('command'),
            'exit_code': -1
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'command': task_data.get('command'),
            'exit_code': -1
        }


def execute_create_structure_worker(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker pour créer une structure de dossiers (picklable, top-level function)

    Args:
        task_data: Dict contenant base_path, folders

    Returns:
        Dict avec le résultat
    """
    try:
        base_path = task_data.get('base_path')
        folders = task_data.get('folders', [])

        if not base_path:
            return {
                'success': False,
                'error': 'base_path manquant'
            }

        # Créer le dossier de base
        os.makedirs(base_path, exist_ok=True)
        created = [base_path]

        # Créer les sous-dossiers
        for folder in folders:
            folder_path = os.path.join(base_path, folder)
            os.makedirs(folder_path, exist_ok=True)
            created.append(folder_path)

        return {
            'success': True,
            'created': created,
            'count': len(created)
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def execute_step_worker(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker principal qui dispatch vers le bon worker selon l'action

    Args:
        task_data: Dict contenant action, et les paramètres nécessaires

    Returns:
        Dict avec le résultat
    """
    action = task_data.get('action')

    if action == 'create_file':
        return execute_create_file_worker(task_data)
    elif action == 'run_command':
        return execute_run_command_worker(task_data)
    elif action == 'create_structure':
        return execute_create_structure_worker(task_data)
    else:
        return {
            'success': False,
            'error': f'Action inconnue: {action}',
            'action': action
        }


def test_worker_pickling():
    """
    Fonction de test pour vérifier que les workers sont bien picklable

    Returns:
        True si tout est OK
    """
    import pickle

    try:
        # Tester le pickling de chaque worker
        pickle.dumps(execute_create_file_worker)
        pickle.dumps(execute_run_command_worker)
        pickle.dumps(execute_create_structure_worker)
        pickle.dumps(execute_step_worker)
        return True
    except Exception as e:
        print(f"Erreur pickling: {e}")
        return False
