"""Test de génération de code pour l'analyseur sémantique (uniquement en cas d'erreur)"""

import subprocess
import os

print("=== Test de génération de code pour l'analyseur sémantique ===")

for i in range(1,2):

    base_dir = os.path.dirname(__file__)
    anasyn_path = os.path.join(base_dir, "src", "anasyn.py")
    test_file = os.path.join(base_dir, "tests", "nnp", f"correct{i}.nno") # change this to your test file path

    # Compilator exeuction
    result = subprocess.run(["python", anasyn_path, test_file], capture_output=True, text=True)
    # Check if the subprocess encountered any errors during execution
    if result.returncode != 0:
        print("❌ Erreur détectée dans anasyn.py :")
        print(result.stderr)

base_dir = os.path.dirname(__file__)
anasyn_path = os.path.join(base_dir, "src", "anasyn.py")
test_file = os.path.join(base_dir, "tests", "nna", f"error1.nno") # change this to your test file path

# Compilator exeuction
result = subprocess.run(["python", anasyn_path, test_file], capture_output=True, text=True)
# Check if the subprocess encountered any errors during execution
if result.returncode != 0:
    print("❌ Erreur détectée dans anasyn.py :")
    print(result.stderr)

