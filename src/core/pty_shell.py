"""
Shell PTY persistant pour un vrai terminal interactif
Utilise pexpect pour maintenir une session bash persistante
"""

import os
import logging
from typing import Dict, Any, Optional
import pexpect
from pathlib import Path
from src.utils.text_processing import (
    strip_ansi_codes,
    clean_command_echo,
    extract_exit_code_from_output
)

logger = logging.getLogger(__name__)


class PersistentShell:
    """
    Shell bash persistant via PTY (pseudo-terminal)

    Contrairement à subprocess.run() qui crée un nouveau processus à chaque fois,
    cette classe maintient UNE session bash persistante où:
    - Les variables d'environnement persistent entre commandes
    - cd fonctionne nativement
    - Aliases et functions shell fonctionnent
    - C'est un VRAI terminal shell interactif
    """

    def __init__(self, shell_path: str = "/bin/bash", timeout: int = 30):
        """
        Initialise une session shell PTY persistante

        Args:
            shell_path: Chemin vers le shell (bash par défaut)
            timeout: Timeout pour les commandes en secondes
        """
        self.shell_path = shell_path
        self.timeout = timeout
        self.shell = None
        self.current_dir = os.getcwd()
        self.prompt_pattern = r'.*[$#] $'  # Pattern pour détecter le prompt

        # Démarrer la session
        self._start_shell()

        logger.info(f"Session PTY démarrée: {shell_path} (PID: {self.shell.pid})")

    def _start_shell(self):
        """Démarre une nouvelle session shell PTY"""
        try:
            # Spawn un shell bash interactif
            self.shell = pexpect.spawn(
                self.shell_path,
                ['-i'],  # Mode interactif
                encoding='utf-8',
                timeout=self.timeout,
                env=os.environ.copy()
            )

            # Attendre le prompt initial de bash
            self.shell.expect([r'.*[$#] ', r'.*[$#]$'], timeout=5)

            # Configurer le prompt pour faciliter la détection
            # PS1 simple sans couleurs pour parsing facile
            self.shell.sendline('export PS1="CoTer> "')
            self.shell.expect('CoTer> ', timeout=5)
            self.prompt_pattern = 'CoTer> '

            # Désactiver Bracketed Paste Mode (empêche les séquences ^[[?2004l/h)
            self.shell.sendline('bind "set enable-bracketed-paste off" 2>/dev/null || true')
            self.shell.expect(self.prompt_pattern, timeout=5)

            # Désactiver l'historique bash (on gère le nôtre) - silencieusement
            self.shell.sendline('unset HISTFILE 2>/dev/null')
            self.shell.expect(self.prompt_pattern, timeout=5)

            # Aller dans le répertoire courant
            self.shell.sendline(f'cd "{self.current_dir}" 2>/dev/null')
            self.shell.expect(self.prompt_pattern, timeout=5)

            # Vider le buffer pour éviter les restes de configuration
            self.shell.buffer = ''
            if hasattr(self.shell, 'before'):
                self.shell.before = ''

            logger.debug("Shell PTY configuré avec succès (mode propre)")

        except Exception as e:
            logger.error(f"Erreur lors du démarrage du shell PTY: {e}")
            raise

    def execute(self, command: str) -> Dict[str, Any]:
        """
        Exécute une commande dans le shell persistant

        Args:
            command: Commande shell à exécuter

        Returns:
            Dict avec 'output', 'success', 'exit_code'
        """
        if not self.shell or not self.shell.isalive():
            logger.warning("Shell PTY mort, redémarrage...")
            self._start_shell()

        try:
            logger.debug(f"Exécution PTY: {command[:100]}")

            # Nettoyer le buffer AVANT d'envoyer la commande (évite race condition)
            # Lire et jeter tout le contenu résiduel du buffer
            try:
                junk = self.shell.read_nonblocking(size=100000, timeout=0)
                if junk:
                    logger.debug(f"[BUFFER NETTOYÉ] Jeté {len(junk)} bytes: {repr(junk[:100])}")
            except:
                pass  # Pas grave si le buffer est vide

            # Envoyer la commande
            self.shell.sendline(command)

            # Attendre le prompt suivant
            index = self.shell.expect([
                self.prompt_pattern,
                pexpect.TIMEOUT,
                pexpect.EOF
            ], timeout=self.timeout)

            if index == 1:  # Timeout
                logger.warning(f"Timeout lors de l'exécution: {command}")
                return {
                    'output': f"Timeout ({self.timeout}s)",
                    'success': False,
                    'exit_code': -1
                }
            elif index == 2:  # EOF (shell fermé)
                logger.error("Shell PTY terminé inopinément")
                self._start_shell()
                return {
                    'output': "Shell terminé, redémarrage...",
                    'success': False,
                    'exit_code': -1
                }

            # Récupérer l'output (tout avant le prompt)
            raw_output = self.shell.before

            # Logs de debug pour diagnostiquer les problèmes
            logger.debug(f"[PTY] RAW OUTPUT (100 premiers chars): {repr(raw_output[:100])}")

            # Nettoyer les séquences ANSI AVANT tout traitement
            clean_output = strip_ansi_codes(raw_output)
            logger.debug(f"[PTY] CLEAN OUTPUT (100 premiers chars): {repr(clean_output[:100])}")

            # Nettoyer l'output (enlever la commande elle-même qui est echo par bash)
            output = clean_command_echo(clean_output, command)
            logger.debug(f"[PTY] FINAL OUTPUT (100 premiers chars): {repr(output[:100])}")

            # Récupérer l'exit code de la dernière commande
            # Vider le buffer AVANT pour isoler cette commande interne
            self.shell.buffer = ''
            if hasattr(self.shell, 'before'):
                self.shell.before = ''

            self.shell.sendline('echo $?')
            self.shell.expect(self.prompt_pattern, timeout=5)

            # Nettoyer l'output de echo $?
            exit_code_raw = self.shell.before
            exit_code_clean = strip_ansi_codes(exit_code_raw)

            # Extraire l'exit code (utilise l'utilitaire centralisé)
            exit_code = extract_exit_code_from_output(exit_code_clean)
            success = (exit_code == 0)

            # Vider le buffer AVANT _update_current_dir() pour l'isoler complètement
            self.shell.buffer = ''
            if hasattr(self.shell, 'before'):
                self.shell.before = ''

            # Mettre à jour le working directory (au cas où cd)
            self._update_current_dir()

            # Vider le buffer APRÈS toutes les commandes internes pour la prochaine commande
            self.shell.buffer = ''
            if hasattr(self.shell, 'before'):
                self.shell.before = ''

            logger.debug(f"Commande terminée - Exit code: {exit_code}, Success: {success}")

            return {
                'output': output,
                'success': success,
                'exit_code': exit_code,
                'command': command
            }

        except Exception as e:
            logger.error(f"Erreur lors de l'exécution PTY: {e}", exc_info=True)
            return {
                'output': f"Erreur PTY: {e}",
                'success': False,
                'exit_code': -1
            }

    def _update_current_dir(self):
        """Met à jour le répertoire courant depuis le shell"""
        try:
            # Vider le buffer AVANT pour isoler cette commande interne
            self.shell.buffer = ''
            if hasattr(self.shell, 'before'):
                self.shell.before = ''

            self.shell.sendline('pwd')
            self.shell.expect(self.prompt_pattern, timeout=5)

            # Nettoyer les séquences ANSI
            pwd_raw = self.shell.before
            pwd_clean = strip_ansi_codes(pwd_raw)
            pwd_lines = [l.strip() for l in pwd_clean.split('\n') if l.strip()]

            # Chercher la ligne qui ressemble à un chemin
            for line in pwd_lines:
                # Ignorer la commande "pwd" elle-même
                if 'pwd' in line.lower():
                    continue
                # Chemin Unix commence par /
                if line.startswith('/'):
                    self.current_dir = line
                    logger.debug(f"Working directory: {self.current_dir}")
                    return
                # Chemin Windows : lettre + : + reste du chemin (ex: C:\Users\...)
                if len(line) > 2 and line[1] == ':' and line[0].isalpha():
                    self.current_dir = line
                    logger.debug(f"Working directory: {self.current_dir}")
                    return

            # Fallback: prendre la deuxième ligne (après "pwd")
            if len(pwd_lines) > 1:
                self.current_dir = pwd_lines[1]

        except Exception as e:
            logger.warning(f"Erreur lors de la mise à jour du cwd: {e}")

    def get_current_directory(self) -> str:
        """Retourne le répertoire courant"""
        return self.current_dir

    def is_alive(self) -> bool:
        """Vérifie si le shell est toujours actif"""
        return self.shell is not None and self.shell.isalive()

    def restart(self):
        """Redémarre la session shell"""
        logger.info("Redémarrage de la session PTY...")
        if self.shell and self.shell.isalive():
            self.shell.close()
        self._start_shell()

    def close(self):
        """Ferme proprement la session shell"""
        if self.shell and self.shell.isalive():
            logger.info("Fermeture de la session PTY...")
            try:
                self.shell.sendline('exit')
                self.shell.expect(pexpect.EOF, timeout=5)
            except:
                pass
            finally:
                self.shell.close()

    def __del__(self):
        """Destructeur - ferme le shell à la destruction de l'objet"""
        self.close()

    def __repr__(self):
        alive = "alive" if self.is_alive() else "dead"
        return f"PersistentShell(pid={self.shell.pid if self.shell else 'N/A'}, {alive}, cwd='{self.current_dir}')"
