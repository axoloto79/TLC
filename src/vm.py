import ast

class VirtualMachine:
    def __init__(self):
        self.ip = -1  # Pointeur de la pile (-1 car pointe vers avant la première case car la pile est vide)
        self.stack = [] # Pile d'exécution
        self.base = -2  # Base du bloc de liaison (-2 car la pile est vide)
        self.pc = 0 # Compteur ordinal
        self.instructions = []

    def load_code(self, lines):
        # Accepte soit des tuples déjà parsés, soit des lignes texte.
        self.instructions = []
        for line in lines:
            if isinstance(line, tuple) and len(line) == 2:
                self.instructions.append([line[0], line[1]])
                continue

            if not isinstance(line, str):
                continue

            line = line.strip()
            if not line or line == "[]":  # Ignorer les lignes vides
                continue

            # Ignorer les lignes qui sont des commentaires/en-têtes
            if "Fonction:" in line or "Addr:" in line or "|" in line:
                continue

            try:
                # Utilise ast.literal_eval pour parser les tuples Python
                instr = ast.literal_eval(line)
                if isinstance(instr, tuple) and len(instr) == 2:
                    self.instructions.append([instr[0], instr[1]])
            except (ValueError, SyntaxError):
                # Si le format n'est pas une string Python littérale, essayer l'ancien format
                if "(" in line and not any(c in line for c in "|:"):
                    parts = line.split("(")
                    if len(parts) == 2:
                        op = parts[0].strip()
                        arg_str = parts[1].replace(")", "").strip()
                        if arg_str == "":
                            self.instructions.append([op, None])
                        elif "," in arg_str:
                            args = arg_str.split(",")
                            try:
                                self.instructions.append([op, (int(args[0].strip()), int(args[1].strip()))])
                            except ValueError:
                                pass  # Ignorer si les arguments ne sont pas des entiers
                        else:
                            try:
                                self.instructions.append([op, int(arg_str)])
                            except ValueError:
                                pass  # Ignorer si l'argument n'est pas un entier

    def load_code_from_file(self, filename):
        with open(filename, "r") as file:
            lines = file.readlines()
            file.close()
        self.instructions = [line.strip().split("(") for line in lines]
        for i in range(len(self.instructions)):
            if self.instructions[i][1] == ")": # si il n'y a pas d'argument
                self.instructions[i][1] = None
            elif "," in self.instructions[i][1]: # si il y a une virgule i.e. il y a 2 arguments
                self.instructions[i][1] = self.instructions[i][1].replace(")", "").split(",")
                self.instructions[i][1] = (int(self.instructions[i][1][0]), int(self.instructions[i][1][1])) # convertit les arguments en entiers
            else: # si il y a un seul argument
                self.instructions[i][1] = int(self.instructions[i][1].replace(")", ""))

    def run(self):
        ##Instruction NNA
        while self.pc < len(self.instructions):
            instr = self.instructions[self.pc]

            self.pc += 1

            op = instr[0]
            arg = instr[1] # None si pas d'argument

            if op == "debutProg":
                self.ip = -1 # initialise le pointeur de la pile
                self.base = -2 # initialise la base du bloc de liaison

            elif op == "finProg":
                print("Fin du programme.")

                return

            elif op == "reserver":
                for _ in range(arg):
                    self.stack.append(None) # alloue une case dans la pile pour la variable
                self.ip += arg # incrémente le pointeur de la pile

            elif op == "empiler":
                self.stack.append(arg)
                self.ip += 1 # incrémente le pointeur de la pile

            elif op == "affectation":
                value = self.stack.pop() # dépile la valeur à affecter
                address = self.stack.pop() # dépile l'adresse de la variable à affecter
                self.stack[address] = value # affecte la valeur à la variable
                self.ip -= 2 # décrémente le pointeur de la pile

            elif op == "valeurPile":
                address = self.stack.pop() # récupère l'adresse de la variable
                value = self.stack[address] # récupère la valeur de la variable
                self.stack.append(value) # empile la valeur

            elif op == "get":
                address = self.stack.pop() # récupère l'adresse de la variable à affecter
                self.stack[address] = int(input("Entrez une valeur entière: "))
                self.ip -= 1 # décrémente le pointeur de la pile

            elif op == "put":
                value = self.stack.pop() # dépile la valeur à afficher
                print(value) # affiche la valeur
                self.ip -= 1 # décrémente le pointeur de la pile

            elif op == "moins":
                self.stack[self.ip] = -self.stack[self.ip] # inverse le signe de la valeur

            elif op == "sous":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a - b)
                self.ip -= 1

            elif op == "add":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a + b)
                self.ip -= 1

            elif op == "mult":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)
                self.ip -= 1

            elif op == "div":
                b = self.stack.pop()
                a = self.stack.pop()
                if b == 0:
                    raise Exception("Division par zéro") # erreur si division par zéro
                self.stack.append(a // b)
                self.ip -= 1

            elif op == "egal":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(int(a == b)) # empile 1 si a == b, sinon 0 ie empile le code de a==b
                self.ip -= 1

            elif op == "diff":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(int(a != b)) # empile 1 si a != b, sinon 0 ie empile le code de a!=b
                self.ip -= 1

            elif op == "inf":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(int(a < b)) #empile 1 si a < b, sinon 0 ie empile le code de a<b
                self.ip -= 1

            elif op == "infeg":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(int(a <= b)) # empile 1 si a <= b, sinon 0 ie empile le code de a<=b
                self.ip -= 1

            elif op == "sup":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(int(a > b)) # empile 1 si a > b, sinon 0 ie empile le code de a>b
                self.ip -= 1

            elif op == "supeg":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(int(a >= b)) # empile 1 si a >= b, sinon 0 ie empile le code de a>=b
                self.ip -= 1

            elif op == "et":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(int(a and b)) # empile 1 si a et b, sinon 0 ie empile le code de a and b
                self.ip -= 1

            elif op == "ou":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(int(a or b)) # empile 1 si a ou b, sinon 0 ie empile le code de a or b
                self.ip -= 1

            elif op == "non":
                a = self.stack.pop()
                self.stack.append(int(not a)) # empile 1 si non a, sinon 0 ie empile le code de not a

            elif op == "tra": # branchement inconditionnel
                self.pc = arg

            elif op == "tze": # branchement si le sommet de la pile est nul
                code = self.stack.pop()
                self.ip -= 1
                if code == 0:
                    self.pc = arg

            elif op == "erreur":
                print("Erreur :", arg)
                print("Arrêt du programme.")
                print("stack: \r\n", self.stack)
                print("pc", self.pc)
                return

            ##Passage aux instructions NNP
            elif op == "empilerAd":
                address_dyn = self.base + 2 + arg # adresse dynamique (+2 pour passer le bloc de liaison est arrivé dans le bloc des paramètre/variables locales)
                self.stack.append(address_dyn) # empile l'adresse dynamique de la variable
                self.ip += 1 # incrémente le pointeur de la pile

            elif op == "reserverBloc":
                self.stack.append(self.base) # empile la base du bloc de liaison précedent
                self.stack.append(None) # reserve une case pour l'adresse de retour
                self.ip += 2 # incremente le pointeur de la pile

            elif op == "traStat":
                a = arg[0]
                nbp = arg[1] # nbp = nombre de paramètres
                self.base = self.ip - nbp -1 # mets à jour la base du bloc de liaison
                self.stack[self.base + 1] = self.pc # mets à jour l'adresse de retour (self.pc-1 ?)
                self.pc = a # mets à jour le pc pour aller à l'instruction suivante de la fonction/procédure

            elif op == "retourFonct":
                valeur = self.stack.pop() # récupère la valeur de retour
                old_base = self.base # récupère l'ancienne valeur de la base
                self.ip = old_base # mets à jour le pointeur de la pile
                self.base = self.stack[old_base] # récupère la base du bloc de liaison précedent et mets à jour la base
                self.pc = self.stack[old_base + 1] # récupère l'adresse de retour et mets à jour le pc
                del self.stack[old_base:] # supprime les cases utilisées par la fonction
                self.stack.append(valeur) # empile la valeur de retour

            elif op == "retourProc":
                old_base = self.base # récupère l'ancienne valeur de la base
                self.base = self.stack[old_base] # récupère la base du bloc de liaison précedent et mets à jour la base
                self.ip = old_base - 1 # mets à jour le pointeur de la pile
                self.pc = self.stack[old_base + 1] # récupère l'adresse de retour et mets à jour le pc
                del self.stack[old_base:] # supprime les case utilisée par la procédure

            elif op == "empilerParam":
                address = arg # adresse du paramètre
                address_dyn = self.base + 2 + address # calcul de l'adresse dynamique du paramètre
                self.stack.append(self.stack[address_dyn]) # empile la valeur de l'adresse du paramètre
                self.ip += 1 # incrémente le pointeur de la pile

            else:
                raise Exception(f"Instruction inconnue : {op}, {arg}") # erreur si tout autre instruction