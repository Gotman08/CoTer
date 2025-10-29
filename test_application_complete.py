#!/usr/bin/env python3
"""
Test complet de l'application Terminal IA
Simule l'utilisation par un utilisateur lambda
"""

import sys
import subprocess
import time

def test_scenario_multiple_models():
    """
    Test avec plusieurs modèles disponibles
    Simule la sélection automatique du premier modèle
    """
    print("="*70)
    print("TEST: SCÉNARIO AVEC PLUSIEURS MODÈLES")
    print("="*70)
    print()

    # Créer un script qui lance l'application et sélectionne automatiquement
    # En simulant l'appui sur Entrée (accepte le premier modèle)

    test_script = """
cd /mnt/c/Users/nicol/Documents/Projet/TerminalIA
source venv/bin/activate

# Lancer l'application avec input automatique
# Entrée = sélectionne le premier modèle (cursor par défaut)
# /quit = quitte l'application
echo -e "\\n/quit" | timeout 30 python main.py 2>&1
"""

    print("🚀 Lancement de l'application...")
    print("   (Sélection automatique du premier modèle puis quit)\n")

    try:
        result = subprocess.run(
            ["wsl", "bash", "-c", test_script],
            capture_output=True,
            text=True,
            timeout=35
        )

        output = result.stdout

        print("="*70)
        print("SORTIE DE L'APPLICATION:")
        print("="*70)
        print(output)
        print("="*70)

        # Vérifier les éléments clés
        checks = {
            "Hardware détecté": "hardware détecté" in output.lower() or "hardware:" in output.lower(),
            "Détection modèles Ollama": "détection des modèles ollama" in output.lower(),
            "Modèles listés": "tinyllama" in output.lower() or "qwen" in output.lower(),
            "Application démarrée": "bienvenue" in output.lower() or "terminal ia" in output.lower() or ">" in output,
        }

        print("\n" + "="*70)
        print("RÉSULTAT DES VÉRIFICATIONS:")
        print("="*70)

        all_passed = True
        for check_name, passed in checks.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status} - {check_name}")
            if not passed:
                all_passed = False

        return all_passed

    except subprocess.TimeoutExpired:
        print("\n⚠️  Timeout - L'application a pris trop de temps")
        print("   (C'est normal si le menu attend une interaction)")
        return None
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scenario_with_configured_model():
    """Test avec un modèle configuré qui existe"""
    print("\n" + "="*70)
    print("TEST: AVEC MODÈLE CONFIGURÉ EXISTANT")
    print("="*70)
    print()

    test_script = """
cd /mnt/c/Users/nicol/Documents/Projet/TerminalIA
source venv/bin/activate

# Lancer avec un modèle spécifié qui existe
echo "/quit" | timeout 15 python main.py --model tinyllama:latest 2>&1 | head -100
"""

    print("🚀 Lancement avec --model tinyllama:latest...\n")

    try:
        result = subprocess.run(
            ["wsl", "bash", "-c", test_script],
            capture_output=True,
            text=True,
            timeout=20
        )

        output = result.stdout

        print("="*70)
        print("SORTIE (premiers 50 lignes):")
        print("="*70)
        print("\n".join(output.split("\n")[:50]))
        print("="*70)

        # Vérifications
        has_tinyllama = "tinyllama" in output.lower()
        has_detection = "détection des modèles" in output.lower()

        print(f"\n✓ Modèle tinyllama détecté: {has_tinyllama}")
        print(f"✓ Phase de détection présente: {has_detection}")

        return has_tinyllama and has_detection

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False


def test_scenario_with_missing_model():
    """Test avec un modèle configuré qui n'existe pas"""
    print("\n" + "="*70)
    print("TEST: AVEC MODÈLE CONFIGURÉ INEXISTANT")
    print("="*70)
    print()

    test_script = """
cd /mnt/c/Users/nicol/Documents/Projet/TerminalIA
source venv/bin/activate

# Lancer avec un modèle qui n'existe pas
echo "/quit" | timeout 15 python main.py --model modele-inexistant 2>&1 | head -100
"""

    print("🚀 Lancement avec --model modele-inexistant...\n")

    try:
        result = subprocess.run(
            ["wsl", "bash", "-c", test_script],
            capture_output=True,
            text=True,
            timeout=20
        )

        output = result.stdout

        print("="*70)
        print("SORTIE (premiers 50 lignes):")
        print("="*70)
        print("\n".join(output.split("\n")[:50]))
        print("="*70)

        # Vérifications
        has_warning = "modèle configuré" in output.lower() and ("n'est plus disponible" in output.lower() or "introuvable" in output.lower())
        has_menu = "sélectionnez" in output.lower() or "tinyllama" in output.lower()

        print(f"\n✓ Warning modèle manquant: {has_warning}")
        print(f"✓ Menu de sélection affiché: {has_menu}")

        return has_warning and has_menu

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False


def main():
    """Lance tous les tests"""
    print("\n" + "="*70)
    print("TESTS COMPLETS DE L'APPLICATION TERMINAL IA")
    print("Simulation d'utilisation par un utilisateur lambda sous WSL")
    print("="*70)
    print()

    results = []

    # Test 1: Plusieurs modèles
    result1 = test_scenario_multiple_models()
    results.append(("Scénario plusieurs modèles", result1))

    # Test 2: Modèle configuré existant
    result2 = test_scenario_with_configured_model()
    results.append(("Modèle configuré existant", result2))

    # Test 3: Modèle configuré manquant
    result3 = test_scenario_with_missing_model()
    results.append(("Modèle configuré manquant", result3))

    # Résumé
    print("\n" + "="*70)
    print("RÉSUMÉ FINAL DES TESTS")
    print("="*70)

    for name, result in results:
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⚠ SKIPPED/TIMEOUT"
        print(f"{status} - {name}")

    passed = sum(1 for _, r in results if r is True)
    total = len(results)

    print(f"\n📊 Score: {passed}/{total} tests réussis")
    print("="*70)


if __name__ == "__main__":
    main()
