import sys
class CodeGenerator:
    """
    Represents a code generator for emitting instructions and managing labels.

    This class provides functionality to build a sequence of instructions with optional
    arguments, generate labels, and reset the current state. The emitted instructions
    can be retrieved or printed as required.

    :ivar instructions: A list that stores all the emitted instructions in sequence.
    :type instructions: list[str]
    :ivar label_counter: A counter used to generate unique labels.
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
        Resets the state of the object by clearing the list of instructions and resetting
        the label counter to its initial value.

        :return: None
        """
        self.instructions = []
        self.label_counter = 0

    def emit(self, opName, arg=None):
        """
        Appends an instruction to the instructions list. The instruction consists of
        an opName and, optionally, an argument. When the argument is provided, it
        is appended alongside the opName in a single formatted string. If no argument
        is provided, only the opName is added.

        :param opName: The operation name to be added to the list of instructions.
        :type opName: str
        :param arg: The optional argument associated with the opName. Defaults to None.
        :type arg: int or (int, int) depend of instruction, optional
        :return: None
        """
        self.instructions.append((opName, arg))
        self.instruction_counter += 1

    def add_identifier(self, name):
        """
        Adds an identifier to the identifier table with a unique index.

        :param name: The name of the identifier to be added.
        :type name: str
        """
        self.identifier_table[name] = self.identifier_counter
        self.identifier_counter += 1


    def print_code(self, output=None):
        """
        Prints the instructions to the given output stream.

        This method iterates over the instructions and writes each to the specified
        output stream. If no output stream is provided, it defaults to using the
        standard output.

        :param output: The output stream to print the instructions. Defaults to
            standard output.
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
        Returns the last operation name from the instructions list.

        :return: The last operation name as a string.
        :rtype: str
        """
        return self.instructions[-1][0] if self.instructions else None # vérifier si la liste est vide avant d'accéder au dernier élément

    def patch_tra_instructions(self, replacement_arg):
        """
        Remplace toutes les instructions 'tra' sans argument par 'tra' avec replacement_arg.

        :param replacement_arg: La valeur entière à utiliser comme argument de remplacement.
        :type replacement_arg: int
        """
        new_instructions = []
        for op, arg in self.instructions:
            if op == "tra" and arg is None:
                new_instructions.append(("tra", replacement_arg))
            else:
                new_instructions.append((op, arg))
        self.instructions = new_instructions
