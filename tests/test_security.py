"""Tests pour le module de sécurité"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.security import SecurityValidator

def test_safe_command():
    """Test d'une commande sûre"""
    validator = SecurityValidator()
    is_valid, risk_level, reason = validator.validate_command("ls -la")

    assert is_valid == True
    assert risk_level == "low"
    print("✅ Test commande sûre: PASSED")

def test_dangerous_command():
    """Test d'une commande dangereuse"""
    validator = SecurityValidator()
    is_valid, risk_level, reason = validator.validate_command("rm -rf /")

    assert is_valid == False
    assert risk_level == "blocked"
    print("✅ Test commande dangereuse: PASSED")

def test_high_risk_command():
    """Test d'une commande à haut risque"""
    validator = SecurityValidator()
    is_valid, risk_level, reason = validator.validate_command("rm test.txt")

    assert is_valid == True
    assert risk_level == "high"
    assert validator.requires_confirmation(risk_level) == True
    print("✅ Test commande à haut risque: PASSED")

def test_medium_risk_command():
    """Test d'une commande à risque moyen"""
    validator = SecurityValidator()
    is_valid, risk_level, reason = validator.validate_command("chmod 755 script.sh")

    assert is_valid == True
    assert risk_level == "medium"
    print("✅ Test commande à risque moyen: PASSED")

def test_sudo_command():
    """Test d'une commande avec sudo"""
    validator = SecurityValidator()
    is_valid, risk_level, reason = validator.validate_command("sudo apt update")

    assert is_valid == True
    assert risk_level == "high"
    print("✅ Test commande sudo: PASSED")

def run_all_tests():
    """Lance tous les tests"""
    print("\n" + "="*60)
    print("TESTS DU MODULE DE SÉCURITÉ")
    print("="*60 + "\n")

    tests = [
        test_safe_command,
        test_dangerous_command,
        test_high_risk_command,
        test_medium_risk_command,
        test_sudo_command
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: FAILED - {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: ERROR - {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Résultats: {passed} passés, {failed} échoués")
    print("="*60 + "\n")

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
