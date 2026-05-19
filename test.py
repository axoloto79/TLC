"""Test de la machine virtuelle avec le code généré pour les tests perso"""

from src.vm import VirtualMachine


vm = VirtualMachine()

vm.load_code_from_file("tests/test_perso/generatedCode")

vm.run()

