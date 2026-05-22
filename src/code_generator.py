import sys
class CodeGenerator:
    """
    Générateur de code pour émettre des instructions et gérer les labels.

    Cette classe permet de construire une séquence d'instructions (avec
    arguments optionnels), générer des labels et réinitialiser l'état.

    :ivar instructions: liste des instructions émises.
    :type instructions: list[str]
    :ivar label_counter: compteur pour générer des labels uniques.
    :type label_counter: int
    """
    def __init__(self):
        self.instructions = []
        self.instruction_counter = 0
        self.identifier_counter = 0
        self.identifier_per_line_counter = 0 #Le nb d'identificateur par ligne, utile pour reserver(n) dans la pile
        self.isInsideProcOrFonct = False #Utile pour savoir si on utilise des adresses local ou globale
        self.identifier_table = {}
        self.fonct_or_proc_ident_begin_table = {} #stocke pr chaque nom de procedure ou fonction l'adresse dans la pile ou elle commence => utile pr les appels de fonction
        self.fonct_or_proc_ident_couter_table = {} #stocke pr chaque nom de procedure ou fonction le nombre de parametres
        self.param_fonct_or_proc_counter = 0 #Stocke le nb de parametre dont a besoin une procedure ou une fonction => utile pr traStat
        self.is_inside_decla_param_fonct_or_proc = True #Permet de savoir si on est dans une déclaration de parametre, permet de stocker les parametres dans une liste et verifier qu'un element est bien dedans pour choisir entre empiler et empilerParam
        self.param_fonct_or_proc = []
        self.is_calling_fonct_or_proc = False #pour savoir si on est dans un appel de fonction pr ne pas appeler valeurPile
        self.isInside = "global" #permet de savoir dans quelle fonction on se trouve

    def set_entry_point(self, name):
        self.entry_point = name

    def reset(self):
        """
        Réinitialise l'état en vidant la liste d'instructions et en remettant
        le compteur de labels à sa valeur initiale.

        :return: None
        """
        self.instructions = []
        self.label_counter = 0

    def emit(self, opName, arg=None):
        """
        Ajoute une instruction à la liste. L'instruction est composée d'un nom
        d'opération et éventuellement d'un argument.

        :param opName: nom de l'opération.
        :type opName: str
        :param arg: argument optionnel (int ou tuple d'int). Par défaut None.
        :return: None
        """
        self.instructions.append((opName, arg))
        self.instruction_counter += 1

    def add_identifier(self, name):
        """
        Ajoute un identificateur à la table avec un index unique.

        :param name: nom de l'identificateur.
        :type name: str
        """
        self.identifier_table[name] = self.identifier_counter
        self.identifier_counter += 1


    def print_code(self, output=None):
        """
        Imprime les instructions sur le flux de sortie donné.

        Parcourt la liste d'instructions et écrit chacune sur le flux fourni
        (par défaut stdout).

        :param output: flux de sortie (optionnel).
        :type output: Optional[IO]
        :return: None
        """
        output = output or sys.stdout
        for instr in self.instructions:
            print(instr, file=output)

    def getInstructions(self):
        return self.instructions

    def get_last_opname(self):
        """
        Retourne le nom de la dernière opération dans la liste d'instructions.

        :return: nom de l'opération (str) ou None si la liste est vide.
        :rtype: str
        """
        return self.instructions[-1][0] if self.instructions else None # vérifier si la liste est vide avant d'accéder au dernier élément

    def patch_tra_instructions(self, replacement_arg):
        """
        Remplace toutes les instructions 'tra' sans argument par 'tra' avec
        l'argument fourni.

        :param replacement_arg: valeur entière utilisée comme argument.
        :type replacement_arg: int
        """
        new_instructions = []
        for op, arg in self.instructions:
            if op == "tra" and arg is None:
                new_instructions.append(("tra", replacement_arg))
            else:
                new_instructions.append((op, arg))
        self.instructions = new_instructions
