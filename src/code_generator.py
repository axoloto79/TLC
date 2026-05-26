import sys
class CodeGenerator:
    def __init__(self):
        self.instructions = []
        self.instruction_counter = 0
        self.identifier_counter = 0
        self.identifier_per_line_counter = 0 
        self.isInsideProcOrFonct = False 
        self.identifier_table = {}
        self.fonct_or_proc_ident_begin_table = {} 
        self.fonct_or_proc_ident_couter_table = {} 
        self.param_fonct_or_proc_counter = 0 
        self.is_inside_decla_param_fonct_or_proc = True 
        self.param_fonct_or_proc = []
        self.is_calling_fonct_or_proc = False 
        self.isInside = "global"

    def set_entry_point(self, name):
        self.entry_point = name

    def reset(self):
        self.instructions = []
        self.label_counter = 0

    def emit(self, opName, arg=None):
        self.instructions.append((opName, arg))
        self.instruction_counter += 1

    def add_identifier(self, name):
        self.identifier_table[name] = self.identifier_counter
        self.identifier_counter += 1

    def print_code(self, output=None):
        output = output or sys.stdout
        for instr in self.instructions:
            print(instr, file=output)

    def getInstructions(self):
        return self.instructions

    def get_last_opname(self):
        return self.instructions[-1][0] if self.instructions else None

    def patch_tra_instructions(self, replacement_arg):
        new_instructions = []
        for op, arg in self.instructions:
            if op == "tra" and arg is None:
                new_instructions.append(("tra", replacement_arg))
            else:
                new_instructions.append((op, arg))
        self.instructions = new_instructions
