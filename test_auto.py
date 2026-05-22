import subprocess
import os
from src.vm import VirtualMachine

print("=== Test de génération de code pour affectations ===")

for i in range(1,5):

    base_dir = os.path.dirname(__file__)
    anasyn_path = os.path.join(base_dir, "src", "anasyn.py")
    test_file = os.path.join(base_dir, "tests", "nna", f"correct{i}.nno") # adapter le chemin si besoin

    # Exécution du compilateur
    result = subprocess.run(["python", anasyn_path, test_file], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Erreur détectée dans anasyn.py :")
        print(result.stderr)
    else:
        lines = result.stdout.strip().split("\n")

        print("code pseudo assembleur généré :")
        for line in lines:
            print(line)

        vm = VirtualMachine()
        vm.load_code(lines)
        vm.run()