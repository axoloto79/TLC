#!/usr/bin/python

## 	@package anasyn
# 	Syntactical Analyser package. 
#

import sys, argparse, re
import logging
from textwrap import indent

import analex

from anasem import SemanticChecker, SemanticException
from code_generator import CodeGenerator

semantic_analyser = SemanticChecker()

logger = logging.getLogger('anasyn')

DEBUG = False
LOGGING_LEVEL = logging.DEBUG


class AnaSynException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class IdentifierTable:
    def __init__(self):
        self.table = {"global": {}}
        self.address_counters = {"global": 0}  # compteur d’adresses par scope
    def modify_global_beginning(self, addr):
        self.address_counters = {"global": 0}

    def _get_next_address(self, scope):
        if scope not in self.address_counters:
            self.address_counters[scope] = 0
        addr = self.address_counters[scope]
        self.address_counters[scope] += 1
        return addr

    def add_global_variable(self, name, var_type):
        addr = self._get_next_address("global")
        self.table["global"][name] = {
            "type": var_type,
            "role": "variable",
            "addr": addr,
            "mode": None
        }

    def add_function(self, name, addr):
        self.table["global"][name] = {"type": "function", "params": [], "adress" : addr}
        self.table[name] = {}
        self.address_counters[name] = 0


    def add_function_param(self, func_name, param_name, param_type="unknown"):
        if func_name not in self.table or func_name not in self.table["global"]:
            raise ValueError(f"Function '{func_name}' not found.")
        self.table["global"][func_name]["params"].append(param_name)
        addr = self._get_next_address(func_name)
        self.table[func_name][param_name] = {
            "type": param_type,
            "role": "parameter",
            "addr": addr,
            "mode": None
        }

    def add_local_variable(self, func_name, var_name, var_type):
        if func_name not in self.table:
            raise ValueError(f"Function '{func_name}' not found in symbol table.")
        addr = self._get_next_address(func_name)
        self.table[func_name][var_name] = {
            "type": var_type,
            "role": "local variable",
            "addr": addr,
            "mode": None
        }

    def get_symbol(self, name, scope="global"):
        if scope in self.table and name in self.table[scope]:
            return self.table[scope][name]
        elif scope != "global" and name in self.table["global"]:
            return self.table["global"][name]
        return None

    def get_function_param_count(self, func_name):
        """Retourne le nombre de paramètres pour une fonction donnée."""
        if func_name not in self.table["global"] or self.table["global"][func_name].get("type") != "function":
            raise ValueError(f"'{func_name}' n'est pas une fonction déclarée.")
        return len(self.table["global"][func_name]["params"])


    def set_unknown_types_in_scope(self, scope, type_name):
        if scope not in self.table:
            raise ValueError(f"Scope '{scope}' not found in symbol table.")
        for symbol in self.table[scope].values():
            if symbol["type"] == "unknown":
                symbol["type"] = type_name

    def set_unknown_mode_in_scope(self, scope, mode_name):
        """Attribue `mode_name` à tous les paramètres (role=parameter) sans mode dans le scope donné."""
        if scope not in self.table:
            raise ValueError(f"Scope '{scope}' not found in symbol table.")
        for symbol in self.table[scope].values():
            if symbol.get("role") == "parameter" and symbol.get("mode") is None:
                symbol["mode"] = mode_name


    def __str__(self):
        lines = ["TABLE DES IDENTIFICATEURS"]

        lines.append("\n--- [Contexte global] ---")
        lines.append(f"  Adresse du bloc global : {self.address_counters.get('global', '?')}")

        for name, info in self.table["global"].items():
            if not isinstance(info, dict) or "type" not in info:
                continue  # ignore les entrées incorrectes comme une adresse mal placée
            if info["type"] == "function":
                addr = info.get("adress", "?")
                lines.append(f"  Fonction: {name}({', '.join(info['params'])}) | Addr: {addr}")
            else:
                lines.append(
                    f"  Variable: {name} : {info['type']} | Addr: {info['addr']} | Mode: {info['mode']}"
                )

        for func_name in self.table:
            if func_name == "global":
                continue
            lines.append(f"\n--- [Contexte de la fonction '{func_name}'] ---")
            for name, info in self.table[func_name].items():
                role = info["role"]
                type_ = info["type"]
                addr = info["addr"]
                mode = info["mode"]
                lines.append(f"  {role.capitalize()} : {name} : {type_} | Addr: {addr} | Mode: {mode}")
        return "\n".join(lines)
    def count_global_variables(self):
        """Retourne le nombre de variables globales dans la table des symboles."""
        return sum(
            1 for symbol in self.table["global"].values()
            if isinstance(symbol, dict) and symbol.get("role") == "variable"
        )



cg = CodeGenerator()
identifierTable = IdentifierTable()
# Fonction pour récupérer la ligne/colonnes de l'erreur
def get_current_position(lexical_analyser):
    try:
        unit = lexical_analyser.lexical_units[lexical_analyser.lexical_unit_index]
        return unit.get_line_index(), unit.get_col_index()
    except:
        return None, None


########################################################################
#### Syntactical Diagrams
########################################################################

def program(lexical_analyser):
    specifProgPrinc(lexical_analyser)
    cg.emit("debutProg", None)
    lexical_analyser.acceptKeyword("is")
    corpsProgPrinc(lexical_analyser)
    cg.patch_tra_instructions(identifierTable.address_counters.get('global', '?')+1)
    cg.emit("finProg", None)
    cg.print_code()


def specifProgPrinc(lexical_analyser):
    lexical_analyser.acceptKeyword("procedure")
    ident = lexical_analyser.acceptIdentifier()
    logger.debug("Name of program : " + ident)



def corpsProgPrinc(lexical_analyser):
    if not lexical_analyser.isKeyword("begin"):
        logger.debug("Parsing declarations")
        partieDecla(lexical_analyser)
        logger.debug("End of declarations")
    lexical_analyser.acceptKeyword("begin")
    #Comme le calcul de l'addresse de debut global est dans décla_var, si on déclare rien l'addresse de début reste à O. On vérifie donc et on met à jour
    if identifierTable.count_global_variables() == 0:
        identifierTable.address_counters["global"] = cg.instruction_counter -1

    if not lexical_analyser.isKeyword("end"):
        logger.debug("Parsing instructions")
        suiteInstr(lexical_analyser)
        logger.debug("End of instructions")

    lexical_analyser.acceptKeyword("end")
    lexical_analyser.acceptFel()
    logger.debug("End of program")


def partieDecla(lexical_analyser):
    if lexical_analyser.isKeyword("procedure") or lexical_analyser.isKeyword("function"):
        cg.emit("tra", None) #On ne sait pas encore ou est le réel début du programme
        listeDeclaOp(lexical_analyser)
        if not lexical_analyser.isKeyword("begin"):
            listeDeclaVar(lexical_analyser)
    else:
        listeDeclaVar(lexical_analyser)


def listeDeclaOp(lexical_analyser):
    declaOp(lexical_analyser)
    lexical_analyser.acceptCharacter(";")
    if lexical_analyser.isKeyword("procedure") or lexical_analyser.isKeyword("function"):
        listeDeclaOp(lexical_analyser)




def declaOp(lexical_analyser):
    if lexical_analyser.isKeyword("procedure"):
        procedure(lexical_analyser)

    if lexical_analyser.isKeyword("function"):
        fonction(lexical_analyser)



def procedure(lexical_analyser):
    lexical_analyser.acceptKeyword("procedure")
    ident = lexical_analyser.acceptIdentifier()
    cg.isInside = ident
    logger.debug("Name of procedure : " + ident)
    cg.isInsideProcOrFonct = True #On est dans une fonction
    identifierTable.add_function(ident, cg.instruction_counter)

    cg.is_inside_decla_param_fonct_or_proc = True
    list_params = partieFormelle(lexical_analyser)
    cg.fonct_or_proc_ident_couter_table[ident] = cg.param_fonct_or_proc_counter
    cg.is_inside_decla_param_fonct_or_proc = False
    cg.fonct_or_proc_ident_begin_table[ident] = cg.instruction_counter
    semantic_analyser.declare_procedure(ident, list_params)
    semantic_analyser.enter_scope(ident)
    for param in semantic_analyser.get_parameters(ident):
        semantic_analyser.declare_variable(param[0], param[1])
        if "in" in param[2]:
            semantic_analyser.init_variable(param[0], param[1])

    lexical_analyser.acceptKeyword("is")

    corpsProc(lexical_analyser)

    cg.isInsideProcOrFonct = False #On n'est plus dans une fonction
    print(cg.param_fonct_or_proc)
    cg.param_fonct_or_proc = [] #On reinitialise la liste des parametres
    cg.identifier_per_line_counter = 0
    cg.identifier_counter = 0
    cg.identifier_table = {}
    cg.isInside = "global"
    cg.emit("retourProc", None)
    semantic_analyser.exit_scope()


def fonction(lexical_analyser):
    lexical_analyser.acceptKeyword("function")
    # Récupère le nom de la fonction
    ident = lexical_analyser.acceptIdentifier()
    cg.isInside = ident
    logger.debug("Name of function : " + ident)
    cg.isInsideProcOrFonct = True #On est dans une fonction
    identifierTable.add_function(ident, cg.instruction_counter)


    cg.is_inside_decla_param_fonct_or_proc = True
    # Récupère les parametres de la fonction
    list_params = partieFormelle(lexical_analyser)
    cg.fonct_or_proc_ident_couter_table[ident] = cg.param_fonct_or_proc_counter
    cg.is_inside_decla_param_fonct_or_proc = False

    lexical_analyser.acceptKeyword("return")
    # Récupère le type de retour de la fonction
    return_type = nnpType(lexical_analyser)

    cg.fonct_or_proc_ident_begin_table[ident] = cg.instruction_counter
    # Ajout dans la table des symboles
    semantic_analyser.declare_function(ident, list_params, return_type)
    semantic_analyser.enter_scope(ident)
    # Déclaration/initialisation des variables locales de la fonction
    for param in semantic_analyser.get_parameters(ident):
        semantic_analyser.declare_variable(param[0], param[1])
        if "in" in param[2]:
            semantic_analyser.init_variable(param[0],param[1])
    lexical_analyser.acceptKeyword("is")
    corpsFonct(lexical_analyser)
    cg.isInsideProcOrFonct = False #On n'est plus dans une fonction
    print(cg.param_fonct_or_proc)

    cg.param_fonct_or_proc = [] #On reinitialise la liste des parametres
    cg.identifier_table = {}
    cg.identifier_per_line_counter = 0
    cg.identifier_counter = 0
    cg.isInside = "global"

    semantic_analyser.exit_scope()

def corpsProc(lexical_analyser):
    if not lexical_analyser.isKeyword("begin"):
        partieDeclaProc(lexical_analyser)
    lexical_analyser.acceptKeyword("begin")
    suiteInstr(lexical_analyser)
    lexical_analyser.acceptKeyword("end")


def corpsFonct(lexical_analyser):
    if not lexical_analyser.isKeyword("begin"):
        partieDeclaProc(lexical_analyser)
    lexical_analyser.acceptKeyword("begin")
    suiteInstrNonVide(lexical_analyser)
    lexical_analyser.acceptKeyword("end")



def partieFormelle(lexical_analyser):
    list_params = []
    lexical_analyser.acceptCharacter("(")
    if not lexical_analyser.isCharacter(")"):
        list_params = listeSpecifFormelles(lexical_analyser)
    lexical_analyser.acceptCharacter(")")
    return list_params


def listeSpecifFormelles(lexical_analyser):
    list_params = specif(lexical_analyser)
    if not lexical_analyser.isCharacter(")"):
        lexical_analyser.acceptCharacter(";")
        list_params += listeSpecifFormelles(lexical_analyser)
    return list_params


def specif(lexical_analyser):
    out=False
    idents = listeIdent(lexical_analyser)
    lexical_analyser.acceptCharacter(":")
    #cg.param_fonct_or_proc_counter +=1
    if lexical_analyser.isKeyword("in"):
        out = mode(lexical_analyser)
    type_var = nnpType(lexical_analyser)
    if out:
        mode_var = ["in","out"]
    else:
        mode_var = ["in"]
    return [(ident,type_var,mode_var) for ident in idents]


def mode(lexical_analyser):
    lexical_analyser.acceptKeyword("in")
    if lexical_analyser.isKeyword("out"):
        lexical_analyser.acceptKeyword("out")
        logger.debug("in out parameter")
        identifierTable.set_unknown_mode_in_scope(cg.isInside, "in out")
        return True
    else:
        logger.debug("in parameter")
        identifierTable.set_unknown_mode_in_scope(cg.isInside, "in")
    return False


def nnpType(lexical_analyser):
    if lexical_analyser.isKeyword("integer"):
        lexical_analyser.acceptKeyword("integer")
        logger.debug("integer type")
        identifierTable.set_unknown_types_in_scope(cg.isInside, "integer")
        return "integer"
    elif lexical_analyser.isKeyword("boolean"):
        lexical_analyser.acceptKeyword("boolean")
        logger.debug("boolean type")
        identifierTable.set_unknown_types_in_scope(cg.isInside, "boolean")
        return "boolean"
    else:
        logger.error("Unknown type found <" + lexical_analyser.get_value() + ">!")
        raise AnaSynException("Unknown type found <" + lexical_analyser.get_value() + ">!")


def partieDeclaProc(lexical_analyser):

    listeDeclaVar(lexical_analyser)


def listeDeclaVar(lexical_analyser):
    declaVar(lexical_analyser)
    if lexical_analyser.isIdentifier():
        listeDeclaVar(lexical_analyser)



def declaVar(lexical_analyser):
    idents = listeIdent(lexical_analyser)
    lexical_analyser.acceptCharacter(":")
    if lexical_analyser.isKeyword("integer"):
        var_type = "integer"
    elif lexical_analyser.isKeyword("boolean"):
        var_type = "boolean"
    else:
        # Erreur si le type n'existe pas dans la déclaration de variable
        # Ex : e,e:a;	"a" pas un type
        raise SemanticException(
            f"Unknown type for declaration of {','.join(idents)}: {lexical_analyser.lexical_units[lexical_analyser.lexical_unit_index].value}")
    nnpType(lexical_analyser)
    lexical_analyser.acceptCharacter(";")
    identifierTable.address_counters["global"] = cg.instruction_counter -1
    cg.emit("reserver", cg.identifier_per_line_counter) #On reserve le nombre d'identificateurs présents sur la ligne
    cg.identifier_per_line_counter = 0 #On remet à 0 au cas ou il y a une autre ligne d'identificateur

    # Déclare les variables au début du programme
    for ident in idents:
        semantic_analyser.declare_variable(ident, var_type)

def listeIdent(lexical_analyser):
    ident = lexical_analyser.acceptIdentifier()
    logger.debug("identifier found: " + str(ident))
    if(cg.isInside != "global"):
        if (cg.is_inside_decla_param_fonct_or_proc):
            identifierTable.add_function_param(cg.isInside, ident)
        else:
            identifierTable.add_local_variable(cg.isInside, ident, "integer")
    else:
        identifierTable.add_global_variable(ident, "unknown")


    cg.add_identifier(ident)
    cg.identifier_per_line_counter+=1
    cg.param_fonct_or_proc_counter +=1
    if cg.is_inside_decla_param_fonct_or_proc == True:
        cg.param_fonct_or_proc.append(ident)

    idents = [ident]
    if lexical_analyser.isCharacter(","):
        lexical_analyser.acceptCharacter(",")
        idents += listeIdent(lexical_analyser)
    return idents


def suiteInstrNonVide(lexical_analyser):
    instr(lexical_analyser)
    if lexical_analyser.isCharacter(";"):
        lexical_analyser.acceptCharacter(";")
        suiteInstrNonVide(lexical_analyser)


def suiteInstr(lexical_analyser):
    if not lexical_analyser.isKeyword("end"):
        suiteInstrNonVide(lexical_analyser)


def instr(lexical_analyser):
    if lexical_analyser.isKeyword("while"):
        boucle(lexical_analyser)
    elif lexical_analyser.isKeyword("if"):
        altern(lexical_analyser)
    elif lexical_analyser.isKeyword("get") or lexical_analyser.isKeyword("put"):
        es(lexical_analyser)
    elif lexical_analyser.isKeyword("return"):
        retour(lexical_analyser)
    elif lexical_analyser.isIdentifier():
        ident = lexical_analyser.acceptIdentifier()
        if lexical_analyser.isSymbol(":="):
            lexical_analyser.acceptSymbol(":=")

            if identifierTable.get_symbol(ident, cg.isInside).get("mode") == "in out":
                cg.emit("empilerParam", cg.identifier_table[ident])

            else: #correction du bug de empiler au lieu de empilerAd
                if cg.isInsideProcOrFonct:
                    cg.emit("empilerAd", cg.identifier_table[ident])
                else:
                    cg.emit("empiler", cg.identifier_table[ident])
            type_ident = expression(lexical_analyser)
            # Regarde si une variable est bien déclarée
            semantic_analyser.check_variable_declared(ident)
            # Regarde si une variable a bien une valeur
            semantic_analyser.init_variable(ident, type_ident)

            cg.emit("affectation", None)
            logger.debug("parsed affectation")
        elif lexical_analyser.isCharacter("("):
            cg.is_calling_fonct_or_proc = True
            cg.emit("reserverBloc", None)
            lexical_analyser.acceptCharacter("(")
            list_params = []
            if not lexical_analyser.isCharacter(")"):
                list_params = listePe(lexical_analyser)
            cg.is_calling_fonct_or_proc = False

            cg.emit("traStat", (identifierTable.get_symbol(ident)["adress"], identifierTable.get_function_param_count(ident)))
            # Check si les types des parametres de la procédure sont les bons
            semantic_analyser.check_parameters(ident, list_params)
            lexical_analyser.acceptCharacter(")")
            logger.debug("parsed procedure call")
        else:
            logger.error("Expecting procedure call or affectation!")
            raise AnaSynException("Expecting procedure call or affectation!")
    else:
        logger.error("Unknown Instruction <" + lexical_analyser.get_value() + ">!")
        raise AnaSynException("Unknown Instruction <" + lexical_analyser.get_value() + ">!")


def listePe(lexical_analyser):
    type_exp = expression(lexical_analyser)
    list_params = []
    if lexical_analyser.isCharacter(","):
        lexical_analyser.acceptCharacter(",")
        list_params = listePe(lexical_analyser)
    # Renvoie la liste des types des parametres
    return [type_exp] + list_params


def expression(lexical_analyser):
    logger.debug("parsing expression: " + str(lexical_analyser.get_value()))

    type_a = exp1(lexical_analyser)
    if lexical_analyser.isKeyword("or"):
        lexical_analyser.acceptKeyword("or")
        type_b = exp1(lexical_analyser)
        cg.emit("ou")
        # Check si les types sont les memes pour cette opération
        semantic_analyser.check_type(type_a, type_b)
    return type_a


def exp1(lexical_analyser):
    type_a = exp2(lexical_analyser)
    if lexical_analyser.isKeyword("and"):
        lexical_analyser.acceptKeyword("and")
        type_b = exp2(lexical_analyser)
        cg.emit("et")
        # Check si les types sont les memes pour cette opération
        semantic_analyser.check_type(type_a, type_b)
        return "boolean"
    return type_a

def exp2(lexical_analyser):
    type_a = exp3(lexical_analyser)
    type_b=None
    if lexical_analyser.isSymbol("<"):
        lexical_analyser.acceptSymbol("<")
        type_b= exp3(lexical_analyser)
        cg.emit("inf", None)
    elif lexical_analyser.isSymbol("<="):
        lexical_analyser.acceptSymbol("<=")
        type_b= exp3(lexical_analyser)
        cg.emit("infeg", None)
    elif lexical_analyser.isSymbol(">"):
        lexical_analyser.acceptSymbol(">")
        type_b= exp3(lexical_analyser)
        cg.emit("sup", None)
    elif lexical_analyser.isSymbol(">="):
        lexical_analyser.acceptSymbol(">=")
        type_b= exp3(lexical_analyser)
        cg.emit("supeg", None)
    elif lexical_analyser.isSymbol("="):
        lexical_analyser.acceptSymbol("=")
        type_b= exp3(lexical_analyser)
        cg.emit("egal", None)
    elif lexical_analyser.isSymbol("/="):
        lexical_analyser.acceptSymbol("/=")
        type_b= exp3(lexical_analyser)
        cg.emit("diff", None)
    if type_b is not None:
        # Check si les types sont les memes pour cette opération
        semantic_analyser.check_type(type_a, type_b)
        return "boolean"
    return type_a


def opRel(lexical_analyser):
    logger.debug("parsing relationnal operator: " + lexical_analyser.get_value())

    if lexical_analyser.isSymbol("<"):
        lexical_analyser.acceptSymbol("<")

    elif lexical_analyser.isSymbol("<="):
        lexical_analyser.acceptSymbol("<=")

    elif lexical_analyser.isSymbol(">"):
        lexical_analyser.acceptSymbol(">")

    elif lexical_analyser.isSymbol(">="):
        lexical_analyser.acceptSymbol(">=")

    elif lexical_analyser.isSymbol("="):
        lexical_analyser.acceptSymbol("=")

    elif lexical_analyser.isSymbol("/="):
        lexical_analyser.acceptSymbol("/=")

    else:
        msg = "Unknown relationnal operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg)


def exp3(lexical_analyser):
    type_a = exp4(lexical_analyser)
    if lexical_analyser.isCharacter("+"):
        lexical_analyser.acceptCharacter("+")
        type_b = exp4(lexical_analyser)
        cg.emit("add", None)
        # Check si les types sont les memes pour cette opération
        semantic_analyser.check_type(type_a, type_b)
    elif lexical_analyser.isCharacter("-"):
        lexical_analyser.acceptCharacter("-")
        type_b = exp4(lexical_analyser)
        cg.emit("sous", None)
        # Check si les types sont les memes pour cette opération
        semantic_analyser.check_type(type_a, type_b)
    return type_a


def opAdd(lexical_analyser):
    logger.debug("parsing additive operator: " + lexical_analyser.get_value())
    if lexical_analyser.isCharacter("+"):
        lexical_analyser.acceptCharacter("+")

    elif lexical_analyser.isCharacter("-"):
        lexical_analyser.acceptCharacter("-")

    else:
        msg = "Unknown additive operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg)


def exp4(lexical_analyser):
    type_a = prim(lexical_analyser)
    if lexical_analyser.isCharacter("*"):
        lexical_analyser.acceptCharacter("*")
        type_b = prim(lexical_analyser)
        cg.emit("mult", None)
        # Check si les types sont les memes pour cette opération
        semantic_analyser.check_type(type_a, type_b)
    elif lexical_analyser.isCharacter("/"):
        lexical_analyser.acceptCharacter("/")
        type_b = prim(lexical_analyser)
        cg.emit("div", None)
        # Check si les types sont les memes pour cette opération
        semantic_analyser.check_type(type_a, type_b)
    return type_a


def opMult(lexical_analyser):
    logger.debug("parsing multiplicative operator: " + lexical_analyser.get_value())
    if lexical_analyser.isCharacter("*"):
        lexical_analyser.acceptCharacter("*")

    elif lexical_analyser.isCharacter("/"):
        lexical_analyser.acceptCharacter("/")

    else:
        msg = "Unknown multiplicative operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg)


def prim(lexical_analyser):
    logger.debug("parsing prim")
    opunaire = ""
    if lexical_analyser.isCharacter("+") or lexical_analyser.isCharacter("-") or lexical_analyser.isKeyword("not"):
        opunaire = lexical_analyser.get_value()
        opUnaire(lexical_analyser)
    ele_prim = elemPrim(lexical_analyser)
    if opunaire == "-":
        cg.emit("moins")
    elif opunaire == "not":
        cg.emit("non")
    # if op == "+" rien à faire
    return ele_prim

def opUnaire(lexical_analyser):
    logger.debug("parsing unary operator: " + lexical_analyser.get_value())
    if lexical_analyser.isCharacter("+"):
        lexical_analyser.acceptCharacter("+")
        #ignorer le + dans le code généré car ne change rien

    elif lexical_analyser.isCharacter("-"):
        lexical_analyser.acceptCharacter("-")

    elif lexical_analyser.isKeyword("not"):
        lexical_analyser.acceptKeyword("not")

    else:
        msg = "Unknown additive operator <" + lexical_analyser.get_value() + ">!"
        logger.error(msg)
        raise AnaSynException(msg)


def elemPrim(lexical_analyser):
    if lexical_analyser.isCharacter("("):
        lexical_analyser.acceptCharacter("(")
        type_exp =  expression(lexical_analyser)
        lexical_analyser.acceptCharacter(")")
        return type_exp
    elif lexical_analyser.isInteger():
        val = lexical_analyser.acceptInteger()
        cg.emit("empiler", val)
        return "integer"
    elif lexical_analyser.isKeyword("true"):
        lexical_analyser.acceptKeyword("true")
        cg.emit("empiler", 1)
        return "boolean"
    elif lexical_analyser.isKeyword("false"):
        lexical_analyser.acceptKeyword("false")
        cg.emit("empiler", 0)
        return "boolean"
    elif lexical_analyser.isIdentifier():
        ident = lexical_analyser.acceptIdentifier()
        list_params = []
        if lexical_analyser.isCharacter("("):  # Appel de fonction
            lexical_analyser.acceptCharacter("(")
            if not lexical_analyser.isCharacter(")"):
                cg.emit("reserverBloc", None)
                list_params = listePe(lexical_analyser)
                cg.emit("traStat", (identifierTable.get_symbol(ident)["adress"], identifierTable.get_function_param_count(ident)))
            lexical_analyser.acceptCharacter(")")
            # Check si les parametres sont bons et renvoie en meme temps le type de retour de la fonction
            return semantic_analyser.check_parameters(ident, list_params)
        else:
            if identifierTable.get_symbol(ident, cg.isInside).get("mode") == "in out":
                print("aaaa",ident)
                cg.emit("empilerParam", cg.identifier_table[ident])
                cg.emit("valeurPile")
            elif cg.is_calling_fonct_or_proc == True:
                cg.emit("empiler", cg.identifier_table[ident])
            elif cg.isInside !=  "global": #On empile l'adresse locale si on est dans une fonction
                cg.emit("empilerAd", cg.identifier_table[ident])
                cg.emit("valeurPile", None)
            else: #On est dans le global
                cg.emit("empiler", cg.identifier_table[ident])
                cg.emit("valeurPile", None)

            # Regarde si une variable a bien une valeur
            semantic_analyser.check_init_variable(ident)
            # Regarde si une variable est bien déclarée (pas obligé en soi) et renvoie son type
            return semantic_analyser.check_variable_declared(ident)
    else:
        raise AnaSynException("Unknown Value!")


def valeur(lexical_analyser):
    if lexical_analyser.isInteger():
        entier = lexical_analyser.acceptInteger()
        cg.emit("empiler", entier)
        return "integer"
    elif lexical_analyser.isKeyword("true"):
        lexical_analyser.acceptKeyword("true")
        cg.emit("empiler", 1)
        return "boolean"
    elif lexical_analyser.isKeyword("false"):
        lexical_analyser.acceptKeyword("false")
        cg.emit("empiler", 0)
        return "boolean"
    else:
        raise AnaSynException("Unknown Value ! Expecting an integer or a boolean value!")


def valBool(lexical_analyser):
    if lexical_analyser.isKeyword("true"):
        lexical_analyser.acceptKeyword("true")
        logger.debug("boolean true value")

    else:
        logger.debug("boolean false value")
        lexical_analyser.acceptKeyword("false")

    return "boolean"


def es(lexical_analyser):
    logger.debug("parsing E/S instruction: " + lexical_analyser.get_value())
    if lexical_analyser.isKeyword("get"):
        lexical_analyser.acceptKeyword("get")
        lexical_analyser.acceptCharacter("(")
        ident = lexical_analyser.acceptIdentifier()
        # Vérifie le type du parametre pour get (parametre entier)
        semantic_analyser.check_variable_declared(ident)
        type_var = semantic_analyser.get_variable_type(ident)
        if type_var != "integer":
            raise SemanticException(f"Type error: GET expects an integer variable, got {type_var}")
        # Initialise la variable après le passage au get
        semantic_analyser.init_variable(ident, "integer")
        lexical_analyser.acceptCharacter(")")
        cg.emit("empiler", cg.identifier_table[ident])
        cg.emit("get", None)
        logger.debug("Call to get " + ident)
    elif lexical_analyser.isKeyword("put"):
        lexical_analyser.acceptKeyword("put")
        lexical_analyser.acceptCharacter("(")
        expr_type = expression(lexical_analyser)
        if expr_type not in ["integer", "boolean"]:
            #Erreur si le type du parametre de put n'est pas in entier ou boolean
            raise SemanticException(f"Type error: PUT expects integer or boolean, got {expr_type}")
        lexical_analyser.acceptCharacter(")")
        cg.emit("put", None)
        logger.debug("Call to put")
    else:
        logger.error("Unknown E/S instruction!")
        raise AnaSynException("Unknown E/S instruction!")


def boucle(lexical_analyser):
    logger.debug("parsing while loop: ")
    lexical_analyser.acceptKeyword("while")
    indexForTRA = cg.instruction_counter

    type_exp = expression(lexical_analyser)
    indexOfTZE = cg.instruction_counter
    cg.emit("tze", None) #On ne sait pas encore à quelle adresse renvoyer car on a pas parcouru la fin de la boucle
    # Check si la condition du while est bien un boolean
    semantic_analyser.check_condition_while(type_exp)

    lexical_analyser.acceptKeyword("loop")
    suiteInstr(lexical_analyser)

    cg.emit("tra", None) #Pareil ici
    indexForTZE = cg.instruction_counter

    lexical_analyser.acceptKeyword("end")

    cg.instructions[-1] = ("tra", indexForTRA)
    cg.instructions[indexOfTZE] = ("tze", indexForTZE)

    logger.debug("end of while loop ")


def altern(lexical_analyser):
    logger.debug("parsing if: ")
    lexical_analyser.acceptKeyword("if")
    havingElse = False
    # Générer l'évaluation de la condition
    type_exp = expression(lexical_analyser)
    indexOfTZE = cg.instruction_counter
    cg.emit("tze", None) #on ne connait pas encore l'adresse à laquelle renvoyer

    # Check si la condition du if est bien un boolean
    semantic_analyser.check_condition_if(type_exp)


    lexical_analyser.acceptKeyword("then")
    suiteInstr(lexical_analyser)

    # Label du else

    if lexical_analyser.isKeyword("else"):
        lexical_analyser.acceptKeyword("else")
        havingElse = True
        cg.emit("tra", None)
        addrOfElseBegining = cg.instruction_counter
        print(addrOfElseBegining)
        suiteInstr(lexical_analyser)

    # Label de fin du if


    lexical_analyser.acceptKeyword("end")
    if havingElse == False:
        cg.instructions[indexOfTZE] = ("tze", cg.instruction_counter)
    else:
        cg.instructions[indexOfTZE] = ("tze", addrOfElseBegining)
        cg.instructions[addrOfElseBegining - 1] = ("tra", cg.instruction_counter)
    logger.debug("end of if")


def retour(lexical_analyser):
    logger.debug("parsing return instruction")
    lexical_analyser.acceptKeyword("return")
    expression(lexical_analyser)
    cg.emit("retourFonct", None)


########################################################################
def main():
    parser = argparse.ArgumentParser(description='Do the syntactical analysis of a NNP program.')
    parser.add_argument('inputfile', type=str, nargs=1, help='name of the input source file')
    parser.add_argument('-o', '--outputfile', dest='outputfile', action='store', \
                        default="", help='name of the output file (default: stdout)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('-d', '--debug', action='store_const', const=logging.DEBUG, \
                        default=logging.INFO, help='show debugging info on output')
    parser.add_argument('-p', '--pseudo-code', action='store_const', const=True, default=False, \
                        help='enables output of pseudo-code instead of assembly code')
    parser.add_argument('--show-ident-table', action='store_true', \
                        help='shows the final identifiers table')
    args = parser.parse_args()

    filename = args.inputfile[0]
    f = None
    try:
        f = open(filename, 'r')
    except:
        print("Error: can\'t open input file!")
        return

    outputFilename = args.outputfile

    # create logger
    LOGGING_LEVEL = args.debug
    logger.setLevel(LOGGING_LEVEL)
    ch = logging.StreamHandler()
    ch.setLevel(LOGGING_LEVEL)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if args.pseudo_code:
        True  #
    else:
        False  #

    lexical_analyser = analex.LexicalAnalyser()

    source_lines = []  # liste contenant chaque ligne du code source pour l'affichage des erreurs
    lineIndex = 0
    for line in f:
        line = line.rstrip('\r\n')
        source_lines.append(line)
        lexical_analyser.analyse_line(lineIndex, line)
        lineIndex += 1
    f.close()

    # launch the analysis of the program
    lexical_analyser.init_analyser()
    # Changement pour permettre l'affichage de la ligne de l'erreur
    try:
        program(lexical_analyser)
    except Exception as e:
        line, col = get_current_position(lexical_analyser)
        if line is not None and line < len(source_lines):
            ligne_code = source_lines[line]
            fleche = " " * col + "^"
            raise SemanticException(
                f"error at line {line + 1}, column {col + 1}:\n{ligne_code}\n{fleche}\n{e}"
            )
        else:
            raise SemanticException(f"error: {e}")

    if args.show_ident_table:
        semantic_analyser.print_symbol_table()

    codeObject = cg.getInstructions()

    if outputFilename != "":
        try:
            output_file = open(outputFilename, 'w')
            for instr in codeObject:
                #Ecriture du code objet dans le fichier de sortie sous le même format utilisé par la VM
                output_file.write(instr[0])
                output_file.write("(")
                if instr[1] is not None:
                    if isinstance(instr[1], tuple):
                        output_file.write(','.join(str(val) for val in instr[1]))
                    else:
                        output_file.write(str(instr[1]))
                output_file.write(")\n")

        except:
            print("Error: can\'t open output file!")
            return
    else:
        output_file = sys.stdout

    if outputFilename != "":
        output_file.close()
    print(cg.fonct_or_proc_ident_begin_table)
    print("Table des identifieurs", cg.identifier_table)
    print( cg.fonct_or_proc_ident_couter_table)
    print("------ IDENTIFIER TABLE ------")
    print(identifierTable)
    print("------ END OF IDENTIFIER TABLE ------")

    print(identifierTable.count_global_variables())

########################################################################

if __name__ == "__main__":
    main()