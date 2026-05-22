"""Test tout les fichiers de test dans le dossier tests (sauf test1 et test2M)
   Permets de visualiser toute les étapes de la compilation 
   (code de base en nna/nnp et résultat de l'execution du code)"""

import ast
import subprocess
import os
from src.vm import VirtualMachine

print("=== Test de génération de code pour l'analyseur sémantique ===")

dir_test = "tests"
dict_file = {}
for root, dirs, files in os.walk(dir_test):
    dict_file[root] = {}
    for file in files:
        print(file)
        if not ( file.startswith('.') or file=="test1" or file=="test2M" or file=='.DS_Store'):
            base_dir = os.path.dirname(__file__)
            anasyn_path = os.path.join(base_dir, "src", "anasyn.py")
            test_file = os.path.join(base_dir, root, file)
            print(f"\nContenu du fichier {test_file}:")
            with open(test_file, 'r') as f:
                print(f.read())
            # Exécution du compilateur
            result = subprocess.run(["python", anasyn_path, test_file], capture_output=True, text=True)
            # Vérifie si le sous-processus a rencontré des erreurs lors de l'exécution
            if result.returncode != 0:
                print(f"❌ Erreur détectée dans {file} :")
                print(result.stderr) # permet l'affichage de l'erreur dans le terminal
            else:
                print("Début du programme")
                lines = result.stdout.strip().split("\n")
                code_lines = []
                for line in lines:
                    try:
                        parsed = ast.literal_eval(line)
                        if isinstance(parsed, tuple) and len(parsed) == 2:
                            code_lines.append(parsed)
                    except Exception:
                        continue  # ignorer les lignes non valides
                # Initialise une machine virtuelle pour exécuter le code généré
                vm = VirtualMachine()
                # Charge le code généré dans la machine virtuelle
                vm.load_code(code_lines)
                # Lance l'exécution du code
                vm.run()


print(dict_file)