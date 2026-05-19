# 🧠 Compilateur NNP + Machine Virtuelle

Ce projet implémente un **compilateur complet** pour un langage algorithmique inspiré d’Ada (`NNP`) ainsi qu’une **machine virtuelle à pile** pour exécuter le code généré.

## 📁 Arborescence

```
compilation/
├── src/
│   ├── analex.py           # Analyse lexicale
│   ├── anasyn.py           # Analyse syntaxique + sémantique + génération de code
│   ├── anasem.py           # Analyse sémantique
│   ├── code_generator.py   # Générateur de code
│   └── vm.py               # Machine virtuelle à pile
├── tests/
│   ├── nna/                # Tests NNA (expressions simples)
│   ├── nnp/                # Tests NNP (fonctions, procédures)
│   └── test_perso/         # Tests personnels (fib, tri, etc.)
├── test_auto_sem.py        # Test automatique (analyse + VM)
├── test_auto.py            # Test automatique (génération + VM)
├── test_final.py           # Test automatique (tous les tests)
└── README.md
```

## 🔍 Composants

### 1. `analex.py` — Analyse Lexicale
Transforme le code source `.nno` en une liste de **tokens** (mots-clés, symboles, entiers, identifiants).

### 2. `anasyn.py` — Analyse Syntaxique, Sémantique et Génération de Code
- Vérifie la structure grammaticale du code (`BNF`).
- Vérifie les règles sémantiques (variables, types, portée, etc.).
- Génère du code objet pseudo-assembleur.
- Génère le tableau des identificateurs.

### 3. `anasem.py` — Analyse Sémantique
- Table des identificateurs hiérarchique.
- Gestion des modes (`in`, `out`, `in out`).
- Détection d’erreurs avec ligne et colonne.

### 4. `code_generator.py` — Génération de Pseudo-code
- Produit du code intermédiaire pour la VM.
- Supporte affectations, opérations, `if`, `while`, fonctions, procédures.

### 5. `vm.py` — Machine Virtuelle à Pile
- Exécute le code pseudo-assembleur.
- Instructions de pile, branchements, affichage, appels.

## 🚀 Exécution

1. Crée un fichier `.nnp` dans `tests/test_perso/` :
```ada
procedure main is
  i : integer;
begin
  i := 0;
  while i < 5 loop
    put(i);
    i := i + 1
  end
end.
```

2. Lance le test :
```bash
python test_auto.py
```

## ✅ Fonctionnalités

| Composant | Statut |
|----------|--------|
| Analyse lexicale | ✅ |
| Analyse syntaxique | ✅ |
| Analyse sémantique | ✅ |
| Affectations, expressions | ✅ |
| Boucles, conditions | ✅ |
| Fonctions, procédures | ✅ |
| Modes in/out | ✅ |
| Table des symboles avec adresses | ✅ |
| Détection d’erreurs détaillée | ✅ |
| Exécution avec VM | ✅ |

## 📂 Test Automatique (`test_auto.py`)
```python
import subprocess
from src.vm import VirtualMachine
import os

base_dir = os.path.dirname(__file__)
anasyn_path = os.path.join(base_dir, "src", "anasyn.py")
test_file = os.path.join(base_dir, "tests", "test_perso", "test_fibo.nnp")

result = subprocess.run(["python", anasyn_path, test_file], capture_output=True, text=True)
if result.returncode != 0:
    print("Erreur :", result.stderr)
else:
    lines = result.stdout.strip().split("\n")
    code_lines = [eval(l) for l in lines if l.startswith("(")]
    vm = VirtualMachine()
    vm.load_code(code_lines)
    vm.run()
```