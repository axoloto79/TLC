class SemanticException(Exception):
    def __init__(self, message):
        super().__init__(message)


class SemanticChecker:
    def __init__(self):
        self.scopes = [{}]  # stack of dicts: one per block
        self.symbols = []  # identifiers recorded
        self.current_scope = "global"

    def enter_scope(self, name):
        self.current_scope = name
        self.scopes.append({})

    def exit_scope(self):
        self.current_scope = "global"
        self.scopes.pop()

    def declare_variable(self, name_var, type_var, mode=None):
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
        for entry in self.symbols:
            if entry["name"] == name_var:
                return entry["mode"]
        raise SemanticException(f"Variable '{name_var}' not found in the symbol table.")
    
    def check_mode(self,name_var,mode):
        if self.get_mode(name_var) != mode:
            raise SemanticException(f"Variable '{name_var}' is used without being declared.")

    def is_variable_declared(self, name_var):
        for scope in reversed(self.scopes):
            if name_var in scope:
                return True
        return False

    def check_variable_declared(self, name_var):
        if not self.is_variable_declared(name_var):
            raise SemanticException(f"Variable '{name_var}' is used without being declared.")
        else:
            return self.get_declared_type(name_var)

    def get_declared_type(self, name):
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                return entry["type"]
        raise SemanticException(f"Identifier '{name}' not found in the symbol table.")

    def check_type(self, type1, type2):
        if type1 != type2:
            raise SemanticException(f"Type error: Operation between '{type1}' and '{type2}' is not allowed.")

    def get_variable_type(self, name):
        for scope in reversed(self.scopes):
            if name in scope and isinstance(scope[name], str):
                return scope[name]
        raise SemanticException(f"Variable '{name}' is not declared.")

    def init_variable(self, name, type_affect):
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                if "out" not in entry["mode"]:
                    raise SemanticException(f"Cannot mark '{name}' as initialized: Variable is input.")
                entry["initialized"] = True
                if entry["type"] != type_affect:
                    raise SemanticException(f"Invalid assignment to '{name}': Expected '{entry['type']}', got '{type_affect}'.")
                return
        raise SemanticException(f"Cannot mark '{name}' as initialized: Variable not declared.")

    def mark_initialized(self, name):
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                entry["initialized"] = True
                return

    def check_init_variable(self, name):
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                if not entry["initialized"]:
                    raise SemanticException(f"Variable '{name}' is used without being initialized.")
                return
        raise SemanticException(f"Variable '{name}' is not declared.")

    def check_condition_if(self, type_cond):
        if type_cond != "boolean":
            raise SemanticException(f"Type error: The if-condition must be a boolean, got '{type_cond}'.")

    def check_condition_while(self, type_cond):
        if type_cond != "boolean":
            raise SemanticException(f"Type error: The while-condition must be a boolean, got '{type_cond}'.")

    def declare_function(self, name, params,type_return):
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
        if name in [symbol["name"] for symbol in self.symbols]:
            raise SemanticException(f"Procedure '{name}' already declared.")
        self.symbols.append({
            "name": name,
            "type": "procedure",
            "scope": self.current_scope,
            "parameters": params,
        })
    
    def get_parameters(self,name):
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                return entry["parameters"]
        raise SemanticException(f"Ident '{name}' not found in the symbol table.")
    
    def check_parameters(self,name,params):
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                params_decla = entry["parameters"]
                if(len(params_decla)!=len(params)):
                    raise SemanticException(f"Invalid number of arguments for '{name}': expected {len(params_decla)}, got {len(params)}")
                for i in range(len(params_decla)):
                    if(params[i]!=params_decla[i][1]):
                        raise SemanticException(f"Invalid type of argument {i} for '{name}': expected {params_decla[i]}, got {params[i]}")
                if entry["type"] == "function":
                    return entry["type_return"]
                elif entry["type"] == "procedure":
                    return None
        raise SemanticException(f"Function '{name}' not found in the symbol table.")

    def print_symbol_table(self):
        print("------ SYMBOL TABLE ------")
        for s in self.symbols:
            print(f"  - {s}")
        print("------ END OF TABLE ------")