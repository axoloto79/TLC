import sys
from pathlib import Path
import anasyn
from vm import VirtualMachine

FILE_TO_COMPILE = "tests/nna/correct1.nno" #Chemin du fichier à compiler

output_path = Path("output/code_objet.co")

sys.argv = ["anasyn.py", FILE_TO_COMPILE, "-o", str(output_path)]

anasyn.main()

vm = VirtualMachine()
vm.load_code_from_file(output_path)
vm.run()