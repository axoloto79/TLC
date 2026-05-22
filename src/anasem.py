class SemanticException(Exception):
    def __init__(self, message):
        super().__init__(message)


class SemanticChecker:
    """
    Gère la phase d'analyse sémantique d'un compilateur/interpréteur :
    tables des symboles par scope, déclarations de variables, vérification
    des types et règles sémantiques.

    :ivar scopes: pile de dictionnaires, chaque dictionnaire représente
        les déclarations de variables d'un bloc ou scope.
    :ivar symbols: liste des identificateurs enregistrés avec leurs attributs
        (nom, type, scope, état d'initialisation).
    :ivar current_scope: nom du scope courant (chaîne).
    """
    def __init__(self):
        self.scopes = [{}]  # stack of dicts: one per block
        self.symbols = []  # identifiers recorded
        self.current_scope = "global"

    def enter_scope(self, name):
        """
        Définit le nom du scope courant et ajoute un nouveau dictionnaire
        vide à la pile des scopes.

        :param name: nom ou identifiant du scope courant.
        :type name: str
        :return: None
        """
        self.current_scope = name
        self.scopes.append({})

    def exit_scope(self):
        """
        Reviens au scope global et retire le dernier scope de la pile.

        :return: None
        """
        self.current_scope = "global"
        self.scopes.pop()

    def declare_variable(self, name_var, type_var, mode=None):
        """
        Déclare une variable dans le scope courant (nom, type, mode).
        Lève une SemanticException si la variable existe déjà dans le scope.

        :param name_var: nom de la variable à déclarer.
        :type name_var: str
        :param type_var: type de la variable.
        :type type_var: Any
        :param mode: liste optionnelle représentant le mode (par défaut ["in","out"]).
        :type mode: list or None
        :return: None
        :raises SemanticException: si la variable est déjà déclarée dans le scope courant.
        """
        if mode is None:
            mode = ["in", "out"]
        if name_var in self.scopes[-1]:
            raise SemanticException(f"Variable '{name_var}' is already declared in this block.")
        self.scopes[-1][name_var] = type_var
        self.symbols.append({
            "name": name_var,
            "type": type_var,
            "scope": self.current_scope,
            "initialized": False,
            "mode": mode,
        })
    def get_mode(self,name_var):
        """
        Récupère le mode d'une variable dans la table des symboles.

        :param name_var: nom de la variable.
        :return: mode de la variable.
        :raises SemanticException: si la variable n'est pas trouvée.
        """
        for entry in self.symbols:
            if entry["name"] == name_var:
                return entry["mode"]
        raise SemanticException(f"Variable '{name_var}' not found in the symbol table.")
    def check_mode(self,name_var,mode):
        """
        Vérifie que la variable est utilisée avec le mode attendu.

        :param name_var: nom de la variable à vérifier.
        :type name_var: str
        :param mode: mode attendu.
        :type mode: str
        :raises SemanticException: si le mode réel ne correspond pas au mode attendu.
        """
        if self.get_mode(name_var) != mode:
            raise SemanticException(f"Variable '{name_var}' is used without being declared.")

    def is_variable_declared(self, name_var):
        """
        Vérifie si une variable est déclarée dans le scope courant ou global.

        :param name_var: nom de la variable.
        :type name_var: str
        :return: True si la variable est déclarée, False sinon.
        :rtype: bool
        """
        for scope in reversed(self.scopes):
            if name_var in scope:
                return True
        return False

    def check_variable_declared(self, name_var):
        """
        Vérifie qu'une variable est déclarée et retourne son type déclaré.

        :param name_var: nom de la variable.
        :type name_var: str
        :return: type déclaré de la variable.
        :rtype: Any
        :raises SemanticException: si la variable est utilisée sans être déclarée.
        """
        if not self.is_variable_declared(name_var):
            raise SemanticException(f"Variable '{name_var}' is used without being declared.")
        else:
            return self.get_declared_type(name_var)

    def get_declared_type(self, name):
        """
        Récupère le type d'une variable/identificateur déclaré dans la table des symboles.

        La recherche se fait en parcourant la table à l'envers pour trouver la déclaration
        la plus récente. Lève une SemanticException si l'identifiant n'est pas trouvé.

        :param name: nom de l'identifiant recherché.
        :type name: str
        :return: type de l'identifiant.
        :rtype: Any
        :raises SemanticException: si l'identifiant n'est pas trouvé.
        """
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                return entry["type"]
        raise SemanticException(f"Identifier '{name}' not found in the symbol table.")

    def check_type(self, type1, type2):
        """
        Vérifie que deux types sont compatibles. Lève une SemanticException si
        les types diffèrent.

        :param type1: premier type à comparer.
        :param type2: second type à comparer.
        :return: None
        :raises SemanticException: si les types ne correspondent pas.
        """
        if type1 != type2:
            raise SemanticException(f"Type error: Operation between '{type1}' and '{type2}' is not allowed.")

    def get_variable_type(self, name):
        """
        Détermine le type d'une variable en parcourant les scopes du plus interne
        au plus externe. Lève une exception si la variable n'est pas déclarée.

        :param name: nom de la variable.
        :type name: str
        :return: type de la variable.
        :rtype: str
        :raises SemanticException: si la variable n'est pas déclarée.
        """
        for scope in reversed(self.scopes):
            if name in scope and isinstance(scope[name], str):
                return scope[name]
        raise SemanticException(f"Variable '{name}' is not declared.")

    def init_variable(self, name, type_affect):
        """
        Marque une variable comme initialisée dans la table des symboles et
        vérifie la cohérence des types.

        Met à jour l'état d'initialisation si la variable est déclarée. Vérifie
        que le type assigné correspond au type déclaré, sinon lève une exception.

        :param name: nom de la variable.
        :type name: str
        :param type_affect: type de la valeur affectée.
        :type type_affect: str
        :return: None
        :raises SemanticException: si la variable n'est pas déclarée ou si les types diffèrent.
        """
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                if "out" not in entry["mode"]:
                    raise SemanticException(f"Cannot mark '{name}' as initialized: Variable is input.")
                entry["initialized"] = True
                if entry["type"] != type_affect:
                    raise SemanticException(
                        f"Invalid assignment to '{name}': Expected '{entry['type']}', got '{type_affect}'.")
                return
        raise SemanticException(f"Cannot mark '{name}' as initialized: Variable not declared.")

    def check_init_variable(self, name):
        """
        Vérifie si une variable a été initialisée. Lève une SemanticException
        si la variable existe mais n'est pas initialisée, ou si elle n'est pas déclarée.

        :param name: nom de la variable (str).
        :return: None
        :raises SemanticException: si la variable n'est pas déclarée ou non initialisée.
        """
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                if not entry["initialized"]:
                    raise SemanticException(f"Variable '{name}' is used without being initialized.")
                return
        raise SemanticException(f"Variable '{name}' is not declared.")

    def check_condition_if(self, type_cond):
        """
        Vérifie que le type de la condition d'un "if" est boolean.
        Lève une SemanticException sinon.

        :param type_cond: type de la condition du if.
        :type type_cond: str
        :raises SemanticException: si le type n'est pas "boolean".
        """
        if type_cond != "boolean":
            raise SemanticException(f"Type error: The if-condition must be a boolean, got '{type_cond}'.")

    def check_condition_while(self, type_cond):
        """
        Vérifie que le type de la condition d'une boucle 'while' est boolean.
        Lève une SemanticException sinon.

        :param type_cond: type de la condition.
        :type type_cond: str
        :raises SemanticException: si le type n'est pas "boolean".
        """
        if type_cond != "boolean":
            raise SemanticException(f"Type error: The while-condition must be a boolean, got '{type_cond}'.")


    def declare_function(self, name, params,type_return):
        """
        Déclare une nouvelle fonction dans la table des symboles en veillant
        à l'unicité du nom dans le scope courant.

        :param name: nom de la fonction.
        :type name: str
        :param params: paramètres de la fonction.
        :type params: Any
        :param type_return: type de retour de la fonction.
        :type type_return: Any
        :raises SemanticException: si une fonction du même nom existe déjà.
        """
        if name in [symbol["name"] for symbol in self.symbols]:
            raise SemanticException(f"Function '{name}' already declared.")
        self.symbols.append({
            "name": name,
            "type": "function",
            "scope": self.current_scope,
            "parameters": params,
            "type_return": type_return,
        })
    def declare_procedure(self, name, params):
        """
        Déclare une nouvelle procédure dans la table des symboles. Lève une
        exception si une procédure du même nom existe déjà.

        :param name: nom de la procédure.
        :type name: str
        :param params: liste des paramètres de la procédure.
        :type params: list[dict]
        :raises SemanticException: si la procédure existe déjà.
        """
        if name in [symbol["name"] for symbol in self.symbols]:
            raise SemanticException(f"Procedure '{name}' already declared.")
        self.symbols.append({
            "name": name,
            "type": "procedure",
            "scope": self.current_scope,
            "parameters": params,
        })
    def get_parameters(self,name):
        """
        Récupère les paramètres d'une fonction ou procédure par son nom depuis
        la table des symboles. Parcourt la table du plus récent au plus ancien.

        :param name: nom de la fonction.
        :type name: str
        :return: paramètres de la fonction.
        :rtype: Any
        :raises SemanticException: si le nom n'est pas trouvé.
        """
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                return entry["parameters"]
        raise SemanticException(f"Ident '{name}' not found in the symbol table.")
    def check_parameters(self,name,params):
        """
        Vérifie la validité des paramètres fournis pour un appel de fonction/procédure
        en les comparant à la déclaration présente dans la table des symboles.

        Assure la correspondance en nombre et en types. Retourne le type de retour
        si c'est une fonction, None si c'est une procédure.

        :param name: nom de la fonction/procédure.
        :type name: str
        :param params: liste des paramètres fournis.
        :type params: list
        :return: type de retour ou None.
        :rtype: Optional[Any]
        :raises SemanticException: en cas de désaccord sur le nombre/types ou si le nom est introuvable.
        """
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                params_decla = entry["parameters"]
                if(len(params_decla)!=len(params)):
                    raise SemanticException(
                        f"Invalid number of arguments for '{name}': expected {len(params_decla)}, got {len(params)}")
                for i in range(len(params_decla)):
                    if(params[i]!=params_decla[i][1]):
                        raise SemanticException(
                            f"Invalid type of argument {i} for '{name}': expected {params_decla[i]}, got {params[i]}")
                if entry["type"] == "function":
                    return entry["type_return"]
                elif entry["type"] == "procedure":
                    return None
        raise SemanticException(f"Function '{name}' not found in the symbol table.")
    # ---------------- SYMBOL TABLE ---------------- #

    def print_symbol_table(self):
        print("------ SYMBOL TABLE ------")
        for s in self.symbols:
            print(f"  - {s}")
        print("------ END OF TABLE ------")