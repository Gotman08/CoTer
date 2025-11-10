#!/usr/bin/env python3
"""
Script de réorganisation automatique du projet CoTer
Effectue une restructuration complète des dossiers et mise à jour des imports

Usage:
    python reorganize_project.py --dry-run    # Simulation sans modification
    python reorganize_project.py              # Exécution réelle
    python reorganize_project.py --rollback   # Annuler les changements

Auteur: Claude Code
Date: 2025-11-10
"""

import os
import sys
import shutil
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse


class ProjectReorganizer:
    """Gestionnaire de réorganisation du projet CoTer"""

    def __init__(self, project_root: Path, dry_run: bool = False):
        self.project_root = project_root
        self.dry_run = dry_run
        self.backup_dir = project_root / f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.changes_log = []
        self.import_map = {}  # {old_import: new_import}

    def log(self, message: str, level: str = "INFO"):
        """Log les actions effectuées"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        prefix = "🔵" if self.dry_run else "✅"
        print(f"[{timestamp}] {prefix} {level}: {message}")
        self.changes_log.append({
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'dry_run': self.dry_run
        })

    def create_backup(self):
        """Crée un backup du projet avant modification"""
        if self.dry_run:
            self.log("Backup serait créé dans: " + str(self.backup_dir), "DRY-RUN")
            return

        self.log(f"Création backup: {self.backup_dir}")
        self.backup_dir.mkdir(exist_ok=True)

        # Sauvegarder uniquement les dossiers importants
        for folder in ['src', 'config', 'tests']:
            src_folder = self.project_root / folder
            if src_folder.exists():
                shutil.copytree(src_folder, self.backup_dir / folder)

        self.log(f"Backup créé avec succès")

    def save_changes_log(self):
        """Sauvegarde le log des changements"""
        log_file = self.project_root / f"reorganization_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.changes_log, f, indent=2, ensure_ascii=False)
        self.log(f"Log sauvegardé: {log_file}")

    # ═══════════════════════════════════════════════════════════════
    # PHASE 1: NETTOYAGE ET RENOMMAGES
    # ═══════════════════════════════════════════════════════════════

    def phase1_cleanup(self):
        """Phase 1: Nettoyage des fichiers redondants"""
        self.log("=" * 60)
        self.log("PHASE 1: NETTOYAGE ET RENOMMAGES")
        self.log("=" * 60)

        # 1.1 Supprimer fichiers backup
        backup_files = [
            'src/modules/autonomous_agent.py.backup'
        ]

        for file_path in backup_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                if not self.dry_run:
                    full_path.unlink()
                self.log(f"Supprimé: {file_path}")
            else:
                self.log(f"Fichier non trouvé: {file_path}", "WARNING")

        # 1.2 Vérifier venv redondants (ne pas supprimer automatiquement)
        venv_dirs = [self.project_root / d for d in ['.venv', 'venv'] if (self.project_root / d).exists()]
        if len(venv_dirs) > 1:
            self.log(f"⚠️  Plusieurs venv détectés: {[str(d.name) for d in venv_dirs]}", "WARNING")
            self.log("   Veuillez supprimer manuellement celui qui n'est pas utilisé", "WARNING")

    def phase1_rename_prompt_managers(self):
        """Renomme les prompt_manager.py pour éviter les conflits"""
        self.log("\n--- Renommage des prompt_manager.py ---")

        # Mapping des renommages
        renames = [
            ('src/core/prompt_manager.py', 'src/core/shell_prompt_manager.py'),
            ('src/terminal/prompt_manager.py', 'src/terminal/terminal_prompt_manager.py')
        ]

        for old_path, new_path in renames:
            old_full = self.project_root / old_path
            new_full = self.project_root / new_path

            if old_full.exists():
                if not self.dry_run:
                    shutil.move(str(old_full), str(new_full))
                self.log(f"Renommé: {old_path} → {new_path}")

                # Enregistrer le mapping pour les imports
                old_import = old_path.replace('/', '.').replace('.py', '')
                new_import = new_path.replace('/', '.').replace('.py', '')
                self.import_map[old_import] = new_import
            else:
                self.log(f"Fichier source non trouvé: {old_path}", "ERROR")

    # ═══════════════════════════════════════════════════════════════
    # PHASE 2: RESTRUCTURATION DES MODULES
    # ═══════════════════════════════════════════════════════════════

    def phase2_restructure_modules(self):
        """Phase 2.1: Restructuration de src/modules/"""
        self.log("\n" + "=" * 60)
        self.log("PHASE 2.1: RESTRUCTURATION DE src/modules/")
        self.log("=" * 60)

        # Définir la nouvelle structure
        modules_structure = {
            'agent': [
                'autonomous_agent.py',
                'agent_orchestrator.py',
                'agent_facades.py',
                'step_executor.py'
            ],
            'planning': [
                'project_planner.py',
                'background_planner.py',
                'plan_storage.py'
            ],
            'execution': [
                'command_executor.py',
                'command_parser.py',
                'code_editor.py'
            ],
            'tools': [
                'git_manager.py',
                'ollama_client.py'
            ]
        }

        # Créer les sous-dossiers et déplacer les fichiers
        modules_dir = self.project_root / 'src' / 'modules'

        for subdir, files in modules_structure.items():
            subdir_path = modules_dir / subdir

            # Créer le dossier
            if not self.dry_run:
                subdir_path.mkdir(exist_ok=True)
                (subdir_path / '__init__.py').touch()
            self.log(f"Créé dossier: src/modules/{subdir}/")

            # Déplacer les fichiers
            for filename in files:
                old_path = modules_dir / filename
                new_path = subdir_path / filename

                if old_path.exists():
                    if not self.dry_run:
                        shutil.move(str(old_path), str(new_path))
                    self.log(f"  Déplacé: {filename} → {subdir}/")

                    # Enregistrer le mapping pour les imports
                    old_import = f"src.modules.{filename[:-3]}"
                    new_import = f"src.modules.{subdir}.{filename[:-3]}"
                    self.import_map[old_import] = new_import
                else:
                    self.log(f"  Fichier non trouvé: {filename}", "WARNING")

    def phase2_restructure_utils(self):
        """Phase 2.2: Restructuration de src/utils/"""
        self.log("\n" + "=" * 60)
        self.log("PHASE 2.2: RESTRUCTURATION DE src/utils/")
        self.log("=" * 60)

        # Définir la nouvelle structure
        utils_structure = {
            'optimization': [
                ('hardware_optimizer.py', 'hardware.py'),
                ('arm_optimizer.py', 'arm.py'),
                ('gc_optimizer.py', 'gc.py')
            ],
            'execution': [
                ('parallel_executor.py', 'parallel_executor.py'),
                ('parallel_workers.py', 'parallel_workers.py'),
                ('command_helpers.py', 'command_helpers.py')
            ],
            'persistence': [
                ('cache_manager.py', 'cache_manager.py'),
                ('user_config.py', 'user_config.py'),
                ('rollback_manager.py', 'rollback_manager.py'),
                ('auto_corrector.py', 'auto_corrector.py')
            ],
            'services': [
                ('ollama_manager.py', 'ollama_manager.py')
            ],
            'helpers': [
                ('logger.py', 'logger.py'),
                ('tag_parser.py', 'tag_parser.py'),
                ('ui_helpers.py', 'ui_helpers.py'),
                ('text_processing.py', 'text_processing.py')
            ]
        }

        # Créer les sous-dossiers et déplacer les fichiers
        utils_dir = self.project_root / 'src' / 'utils'

        for subdir, files in utils_structure.items():
            subdir_path = utils_dir / subdir

            # Créer le dossier
            if not self.dry_run:
                subdir_path.mkdir(exist_ok=True)
                (subdir_path / '__init__.py').touch()
            self.log(f"Créé dossier: src/utils/{subdir}/")

            # Déplacer les fichiers
            for old_filename, new_filename in files:
                old_path = utils_dir / old_filename
                new_path = subdir_path / new_filename

                if old_path.exists():
                    if not self.dry_run:
                        shutil.move(str(old_path), str(new_path))
                    self.log(f"  Déplacé: {old_filename} → {subdir}/{new_filename}")

                    # Enregistrer le mapping pour les imports
                    old_import = f"src.utils.{old_filename[:-3]}"
                    new_import = f"src.utils.{subdir}.{new_filename[:-3]}"
                    self.import_map[old_import] = new_import
                else:
                    self.log(f"  Fichier non trouvé: {old_filename}", "WARNING")

    # ═══════════════════════════════════════════════════════════════
    # MISE À JOUR DES IMPORTS
    # ═══════════════════════════════════════════════════════════════

    def update_imports_in_file(self, file_path: Path) -> int:
        """Met à jour les imports dans un fichier"""
        if not file_path.exists() or file_path.suffix != '.py':
            return 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            changes_count = 0

            # Parcourir tous les mappings d'imports
            for old_import, new_import in self.import_map.items():
                # Patterns de remplacement pour différents types d'imports
                patterns = [
                    # from old_import import X
                    (rf'from {re.escape(old_import)} import', f'from {new_import} import'),
                    # import old_import
                    (rf'import {re.escape(old_import)}\b', f'import {new_import}'),
                    # import old_import as X
                    (rf'import {re.escape(old_import)} as', f'import {new_import} as'),
                ]

                for pattern, replacement in patterns:
                    if re.search(pattern, content):
                        content = re.sub(pattern, replacement, content)
                        changes_count += 1

            # Écrire uniquement si changements
            if content != original_content and not self.dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            return changes_count

        except Exception as e:
            self.log(f"Erreur lors de la mise à jour de {file_path}: {e}", "ERROR")
            return 0

    def update_all_imports(self):
        """Met à jour tous les imports dans le projet"""
        self.log("\n" + "=" * 60)
        self.log("MISE À JOUR DES IMPORTS")
        self.log("=" * 60)

        if not self.import_map:
            self.log("Aucun import à mettre à jour", "WARNING")
            return

        self.log(f"Nombre de mappings d'imports: {len(self.import_map)}")

        # Parcourir tous les fichiers Python
        total_files = 0
        total_changes = 0

        for folder in ['src', 'config', 'tests', '.']:
            folder_path = self.project_root / folder
            if not folder_path.exists():
                continue

            for py_file in folder_path.rglob('*.py'):
                # Ignorer les backups et venv
                if '.backup' in str(py_file) or 'venv' in str(py_file) or '__pycache__' in str(py_file):
                    continue

                changes = self.update_imports_in_file(py_file)
                if changes > 0:
                    total_files += 1
                    total_changes += changes
                    self.log(f"  ✓ {py_file.relative_to(self.project_root)}: {changes} import(s) mis à jour")

        self.log(f"\nRésumé: {total_changes} imports mis à jour dans {total_files} fichiers")

    # ═══════════════════════════════════════════════════════════════
    # EXÉCUTION PRINCIPALE
    # ═══════════════════════════════════════════════════════════════

    def run(self):
        """Exécute la réorganisation complète"""
        try:
            self.log("\n" + "━" * 60)
            self.log("DÉBUT DE LA RÉORGANISATION DU PROJET COTER")
            self.log("━" * 60)

            if self.dry_run:
                self.log("⚠️  MODE DRY-RUN: Aucune modification ne sera effectuée", "WARNING")
            else:
                self.log("Mode exécution réelle - Les modifications seront permanentes", "INFO")

            # Créer backup
            if not self.dry_run:
                self.create_backup()

            # Phase 1: Nettoyage
            self.phase1_cleanup()
            self.phase1_rename_prompt_managers()

            # Phase 2: Restructuration
            self.phase2_restructure_modules()
            self.phase2_restructure_utils()

            # Mise à jour des imports
            self.update_all_imports()

            # Sauvegarder le log
            self.save_changes_log()

            self.log("\n" + "━" * 60)
            self.log("✅ RÉORGANISATION TERMINÉE AVEC SUCCÈS")
            self.log("━" * 60)

            if not self.dry_run:
                self.log(f"Backup disponible dans: {self.backup_dir}")
                self.log("\nPROCHAINES ÉTAPES:")
                self.log("1. Testez l'application: python main.py")
                self.log("2. Si tout fonctionne: git add . && git commit")
                self.log(f"3. Si problème: python reorganize_project.py --rollback")
            else:
                self.log("\nPour appliquer réellement les changements:")
                self.log("  python reorganize_project.py")

        except Exception as e:
            self.log(f"ERREUR CRITIQUE: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def rollback(self):
        """Annule les changements en restaurant le backup le plus récent"""
        self.log("ROLLBACK: Recherche du dernier backup...")

        # Trouver le backup le plus récent
        backups = sorted(self.project_root.glob('.backup_*'), reverse=True)

        if not backups:
            self.log("Aucun backup trouvé!", "ERROR")
            return

        latest_backup = backups[0]
        self.log(f"Backup trouvé: {latest_backup}")

        if self.dry_run:
            self.log(f"Restaurerait depuis: {latest_backup}", "DRY-RUN")
            return

        # Confirmer avec l'utilisateur
        print("\n⚠️  ATTENTION: Cette action va restaurer le projet à son état précédent")
        print(f"Backup: {latest_backup}")
        response = input("Continuer? (oui/non): ").strip().lower()

        if response not in ['oui', 'o', 'yes', 'y']:
            self.log("Rollback annulé par l'utilisateur")
            return

        # Restaurer les dossiers
        for folder in ['src', 'config', 'tests']:
            src_backup = latest_backup / folder
            dest_folder = self.project_root / folder

            if src_backup.exists():
                # Supprimer le dossier actuel
                if dest_folder.exists():
                    shutil.rmtree(dest_folder)

                # Restaurer depuis le backup
                shutil.copytree(src_backup, dest_folder)
                self.log(f"Restauré: {folder}/")

        self.log("✅ ROLLBACK TERMINÉ")
        self.log(f"Le backup reste disponible dans: {latest_backup}")


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="Script de réorganisation automatique du projet CoTer"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulation sans modification réelle'
    )
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Annule les changements en restaurant le dernier backup'
    )

    args = parser.parse_args()

    # Détecter le dossier racine du projet
    project_root = Path(__file__).parent.absolute()

    # Créer le réorganisateur
    reorganizer = ProjectReorganizer(project_root, dry_run=args.dry_run)

    # Exécuter
    if args.rollback:
        reorganizer.rollback()
    else:
        reorganizer.run()


if __name__ == '__main__':
    main()
