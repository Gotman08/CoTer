#!/usr/bin/env python3
"""Script de test pour vérifier le fonctionnement sous WSL"""

import multiprocessing
import time
from config import constants


def test_worker(task_id):
    """Worker de test simple"""
    time.sleep(0.1)
    return {'task_id': task_id, 'result': task_id * 2}


def test_multiprocessing():
    """Test du multiprocessing avec ProcessPoolExecutor"""
    print("="*60)
    print("TEST MULTIPROCESSING SOUS WSL")
    print("="*60)

    # Configuration multiprocessing
    try:
        current_method = multiprocessing.get_start_method(allow_none=True)
        if current_method is None:
            multiprocessing.set_start_method(constants.PARALLEL_PROCESS_START_METHOD, force=False)
            print(f"✓ Méthode multiprocessing configurée: {constants.PARALLEL_PROCESS_START_METHOD}")
        else:
            print(f"✓ Méthode multiprocessing déjà configurée: {current_method}")
    except Exception as e:
        print(f"⚠️  Avertissement configuration multiprocessing: {e}")

    # Test avec ProcessPoolExecutor
    print(f"\nTest avec {multiprocessing.cpu_count()} CPU cores disponibles")

    from concurrent.futures import ProcessPoolExecutor

    tasks = list(range(10))
    results = []

    try:
        start_time = time.time()

        with ProcessPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(test_worker, task_id) for task_id in tasks]
            for future in futures:
                results.append(future.result())

        elapsed = time.time() - start_time

        print(f"✓ {len(results)} tâches exécutées en {elapsed:.2f}s")
        print(f"✓ Résultats: {[r['result'] for r in results[:5]]}... (premiers 5)")
        print("\n✓ MULTIPROCESSING FONCTIONNE CORRECTEMENT SOUS WSL!")

    except Exception as e:
        print(f"\n❌ Erreur lors du test multiprocessing: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_ollama_functions():
    """Test des fonctions de sélection Ollama"""
    print("\n" + "="*60)
    print("TEST FONCTIONS OLLAMA")
    print("="*60)

    try:
        from main import check_ollama_connection, format_model_size

        # Test format_model_size
        assert format_model_size(1024) == "1.0 KB"
        assert format_model_size(1024*1024) == "1.0 MB"
        assert format_model_size(1024*1024*1024) == "1.0 GB"
        print("✓ format_model_size() fonctionne correctement")

        # Test connexion Ollama (ne va probablement pas marcher sans Ollama lancé)
        print("\nTest de connexion Ollama (peut échouer si Ollama n'est pas lancé):")
        host = "http://localhost:11434"
        is_connected = check_ollama_connection(host)
        if is_connected:
            print(f"✓ Ollama est accessible sur {host}")
        else:
            print(f"⚠️  Ollama n'est pas accessible sur {host} (normal si non démarré)")

        print("\n✓ FONCTIONS OLLAMA OK!")
        return True

    except Exception as e:
        print(f"\n❌ Erreur lors du test Ollama: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Lance tous les tests"""
    print("\n" + "="*60)
    print("TESTS COMPLETS SOUS WSL")
    print("="*60)
    print()

    results = []

    # Test 1: Multiprocessing
    results.append(("Multiprocessing", test_multiprocessing()))

    # Test 2: Fonctions Ollama
    results.append(("Fonctions Ollama", test_ollama_functions()))

    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ DES TESTS")
    print("="*60)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {name}")

    all_passed = all(success for _, success in results)

    if all_passed:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
    else:
        print("\n⚠️  CERTAINS TESTS ONT ÉCHOUÉ")

    print("="*60)


if __name__ == "__main__":
    main()
