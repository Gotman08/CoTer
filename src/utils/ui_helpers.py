"""Utilitaires pour l'interface utilisateur et l'affichage"""

from typing import Dict, List, Any, Optional


class UIFormatter:
    """Formateur pour l'affichage dans le terminal"""

    @staticmethod
    def print_section_header(title: str, width: int = 60):
        """
        Affiche un en-tête de section

        Args:
            title: Titre de la section
            width: Largeur de l'en-tête
        """
        print("\n" + "=" * width)
        print(title)
        print("=" * width)

    @staticmethod
    def print_key_value(key: str, value: Any, indent: int = 0):
        """
        Affiche une paire clé-valeur formatée

        Args:
            key: Clé à afficher
            value: Valeur à afficher
            indent: Niveau d'indentation
        """
        indent_str = "   " * indent
        print(f"{indent_str}{key}: {value}")

    @staticmethod
    def print_stats_table(stats: Dict[str, Any], title: str = "", width: int = 60):
        """
        Affiche un tableau de statistiques

        Args:
            stats: Dictionnaire de statistiques
            title: Titre du tableau
            width: Largeur du tableau
        """
        if title:
            UIFormatter.print_section_header(title, width)

        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"\n{key}:")
                UIFormatter.print_stats_table(value, "", width)
            elif isinstance(value, list):
                print(f"\n{key}:")
                for item in value:
                    print(f"   • {item}")
            else:
                UIFormatter.print_key_value(key, value)

    @staticmethod
    def print_warning(message: str):
        """Affiche un message d'avertissement"""
        print(f"⚠️  {message}")

    @staticmethod
    def print_error(message: str):
        """Affiche un message d'erreur"""
        print(f"❌ {message}")

    @staticmethod
    def print_success(message: str):
        """Affiche un message de succès"""
        print(f"✅ {message}")

    @staticmethod
    def print_info(message: str):
        """Affiche un message d'information"""
        print(f"ℹ️  {message}")

    @staticmethod
    def format_percentage(value: float) -> str:
        """Formate un pourcentage"""
        return f"{value:.1f}%"

    @staticmethod
    def format_size_mb(size_bytes: int) -> str:
        """Formate une taille en MB"""
        return f"{size_bytes / (1024 * 1024):.2f} MB"

    @staticmethod
    def format_datetime(dt_string: str) -> str:
        """Formate une date/heure (prend les 19 premiers caractères)"""
        return dt_string[:19] if dt_string else "N/A"


class StatsDisplayer:
    """Afficheur de statistiques pour les différents modules"""

    def __init__(self, formatter: Optional[UIFormatter] = None):
        self.formatter = formatter or UIFormatter()

    def display_cache_stats(self, stats: Dict[str, Any]):
        """
        Affiche les statistiques du cache

        Args:
            stats: Statistiques du cache
        """
        self.formatter.print_section_header("📊 STATISTIQUES DU CACHE OLLAMA")

        if not stats or not stats.get('enabled'):
            self.formatter.print_warning("Le cache n'est pas disponible")
            return

        if 'error' in stats:
            self.formatter.print_error(f"Erreur: {stats['error']}")
            return

        print(f"\n📦 Entrées totales      : {stats.get('total_entries', 0)}")
        print(f"💾 Taille utilisée      : {stats.get('total_size_mb', 0)} MB / {stats.get('max_size_mb', 0)} MB")
        print(f"📈 Utilisation          : {stats.get('usage_percent', 0)}%")
        print(f"🎯 Taux de hits (approx): {stats.get('hit_rate_approx', 0)}%")
        print(f"🔄 Total d'accès        : {stats.get('total_accesses', 0)}")
        print(f"⏱️  TTL (durée de vie)  : {stats.get('ttl_hours', 0)} heures")
        print(f"♻️  Stratégie d'éviction: {stats.get('eviction_strategy', 'N/A').upper()}")

        if stats.get('oldest_entry'):
            print(f"\n📅 Plus ancienne entrée : {self.formatter.format_datetime(stats['oldest_entry'])}")
        if stats.get('latest_entry'):
            print(f"📅 Plus récente entrée  : {self.formatter.format_datetime(stats['latest_entry'])}")

        print("\n" + "=" * 60)

    def display_security_report(self, report: Dict[str, Any]):
        """
        Affiche le rapport de sécurité

        Args:
            report: Rapport de sécurité
        """
        self.formatter.print_section_header("🔒 RAPPORT DE SÉCURITÉ")

        if report.get('total_commands') == 0:
            self.formatter.print_warning("Aucune commande exécutée")
            print("=" * 60)
            return

        print(f"\n📊 Total commandes    : {report['total_commands']}")
        print(f"✅ Taux de succès     : {report['success_rate']}%")
        print(f"\n🔐 Répartition par risque:")
        print(f"   🟢 Faible risque   : {report['low_risk']}")
        print(f"   🟡 Risque moyen    : {report['medium_risk']}")
        print(f"   🔴 Haut risque     : {report['high_risk']}")
        print(f"   ⛔ Bloquées        : {report['blocked']}")

        print(f"\n📈 Compteurs (dernière heure):")
        print(f"   ❌ Échecs          : {report['failed_count']}")
        print(f"   ⚠️  Haut risque    : {report['high_risk_count']}")

        alerts = report.get('alerts', [])
        if alerts:
            print(f"\n⚠️  ALERTES DE SÉCURITÉ:")
            for alert in alerts:
                print(f"   {alert}")
        else:
            print(f"\n✅ Aucune alerte de sécurité")

        print("\n" + "=" * 60)

    def display_rollback_stats(self, stats: Dict[str, Any]):
        """
        Affiche les statistiques de rollback

        Args:
            stats: Statistiques de rollback
        """
        self.formatter.print_section_header("📊 STATISTIQUES ROLLBACK")

        print(f"\n📦 Snapshots totaux   : {stats.get('count', 0)}")
        print(f"💾 Espace utilisé     : {stats.get('total_size_mb', 0)} MB")
        print(f"📁 Répertoire snapshots: {stats.get('snapshots_dir', 'N/A')}")

        print("\n" + "=" * 60)

    def display_correction_stats(self, stats: Dict[str, Any]):
        """
        Affiche les statistiques d'auto-correction

        Args:
            stats: Statistiques d'auto-correction
        """
        self.formatter.print_section_header("🔧 STATISTIQUES D'AUTO-CORRECTION")

        if stats.get('total_errors') == 0:
            self.formatter.print_success("Aucune erreur détectée")
            print("   Le système d'auto-correction n'a pas encore été utilisé")
            print("=" * 60)
            return

        print(f"\n📊 Erreurs analysées  : {stats['total_errors']}")
        print(f"🔧 Auto-corrigeables  : {stats['auto_fixable']} ({stats['auto_fixable_percent']}%)")
        print(f"✨ Haute confiance   : {stats['high_confidence']} ({stats['high_confidence_percent']}%)")

        print(f"\n📋 Répartition par type:")
        error_types = stats.get('error_types', {})
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {error_type:20} : {count}")

        print(f"\n💡 Le système a tenté de corriger automatiquement {stats['auto_fixable']} erreurs")
        print(f"   Utilisez /corrections last pour voir la dernière erreur analysée")

        print("\n" + "=" * 60)

    def display_error_analysis(self, analysis: Dict[str, Any]):
        """
        Affiche l'analyse d'une erreur

        Args:
            analysis: Analyse de l'erreur
        """
        self.formatter.print_section_header("🔍 DERNIÈRE ERREUR ANALYSÉE")

        if not analysis:
            self.formatter.print_success("Aucune erreur récente")
            print("=" * 60)
            return

        print(f"\n📝 Commande originale : {analysis['original_command']}")
        print(f"❌ Type d'erreur      : {analysis['error_type']}")
        print(f"🔢 Code de sortie     : {analysis['exit_code']}")
        print(f"⏰ Timestamp          : {self.formatter.format_datetime(analysis['timestamp'])}")

        if analysis.get('auto_fix'):
            print(f"\n🔧 Correction proposée: {analysis['auto_fix']}")
            print(f"💯 Confiance          : {int(analysis['confidence'] * 100)}%")
            print(f"🔄 Retry possible     : {'Oui' if analysis['can_retry'] else 'Non'}")

        suggestions = analysis.get('suggestions', [])
        if suggestions:
            print(f"\n💡 Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. {suggestion}")

        details = analysis.get('error_details', {})
        if details:
            print(f"\n📋 Détails:")
            for key, value in details.items():
                print(f"   • {key}: {value}")

        print("\n" + "=" * 60)

    def display_snapshots_list(self, snapshots: List[Dict[str, Any]]):
        """
        Affiche la liste des snapshots

        Args:
            snapshots: Liste des snapshots
        """
        self.formatter.print_section_header("📸 SNAPSHOTS DISPONIBLES")

        if not snapshots:
            self.formatter.print_warning("Aucun snapshot disponible")
            print("   Les snapshots sont créés automatiquement avant chaque exécution")
            return

        print(f"\n📦 {len(snapshots)} snapshot(s) disponible(s):\n")

        for i, snapshot in enumerate(snapshots, 1):
            print(f"{i}. {snapshot['snapshot_id']}")
            print(f"   Projet: {snapshot['project_name']}")
            print(f"   Date: {self.formatter.format_datetime(snapshot['datetime'])}")
            print(f"   Description: {snapshot['description']}")
            print()

        print("Pour restaurer: /rollback restore [snapshot_id]")
        print("=" * 60)


class InputValidator:
    """Validation des entrées utilisateur"""

    @staticmethod
    def confirm_action(message: str, default: bool = False) -> bool:
        """
        Demande confirmation à l'utilisateur

        Args:
            message: Message de confirmation
            default: Valeur par défaut

        Returns:
            True si l'utilisateur confirme
        """
        response = input(f"\n{message} (oui/non): ").strip().lower()
        return response in ['oui', 'o', 'yes', 'y']

    @staticmethod
    def parse_command_args(command: str) -> tuple[str, list[str]]:
        """
        Parse une commande et ses arguments

        Args:
            command: Commande complète

        Returns:
            Tuple (commande_base, arguments)
        """
        parts = command.split()
        cmd = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        return cmd, args
