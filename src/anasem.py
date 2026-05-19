class SemanticException(Exception):
    def __init__(self, message):
        super().__init__(message)


class SemanticChecker:
    """
    Manages the semantic analysis phase of a language compiler or interpreter by
    handling scoped symbol tables, variable declaration, type checking, and
    semantic rules verification.


    :ivar scopes: A stack of dictionaries, where each dictionary represents
        variable declarations within a specific block or scope. FOR NNP, TO DO
    :ivar symbols: List of recorded identifiers with their attributes such as
        names, types, scopes, and initialization status.
    :ivar current_scope: The active scope name as a string.
    """
    def __init__(self):
        self.scopes = [{}]  # stack of dicts: one per block
        self.symbols = []  # identifiers recorded
        self.current_scope = "global"

    def enter_scope(self, name):
        """
        Manages the assignment of the current scope name and appends a new,
        empty dictionary to the list of scopes.

        :param name: The name or identifier of the current scope.
        :type name: str
        :return: None
        """
        self.current_scope = name
        self.scopes.append({})

    def exit_scope(self):
        """
        Updates the current scope to a global level and removes the latest scope from
        the stack of scopes. This method is used to exit the current scope and revert
        to the global scope while managing the stack of nested scopes.

        :return: None
        """
        self.current_scope = "global"
        self.scopes.pop()

    def declare_variable(self, name_var, type_var, mode=None):
        """
        Declares a variable in the current scope with its name, type, and mode. If the variable
        already exists in the current scope, it raises a SemanticException. This method also
        appends the variable's details to the symbol table, keeping track of its scope, initialization
        status, and mode.

        :param name_var: Name of the variable to be declared.
        :type name_var: str
        :param type_var: Type of the variable being declared.
        :type type_var: Any
        :param mode: An optional list representing the mode of the variable. Defaults to ["in", "out"].
        :type mode: list or None
        :return: None
        :rtype: NoneType
        :raises SemanticException: If the variable is already declared in the current scope.
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
        Retrieves the mode of a variable from the symbol table.

        :param name_var: The name of the variable whose mode is to be retrieved.
        :return: The mode of the variable with the specified name.
        :raises SemanticException: If the variable with the specified name is
            not found in the symbol table.
        """
        for entry in self.symbols:
            if entry["name"] == name_var:
                return entry["mode"]
        raise SemanticException(f"Variable '{name_var}' not found in the symbol table.")
    def check_mode(self,name_var,mode):
        """
        Checks if the specified variable is used with the correct mode.

        :param name_var: The name of the variable to check.
        :type name_var: str
        :param mode: The expected mode of the variable.
        :type mode: str
        :raises SemanticException: If the actual mode of the variable
            does not match the expected mode.
        """
        if self.get_mode(name_var) != mode:
            raise SemanticException(f"Variable '{name_var}' is used without being declared.")

    def is_variable_declared(self, name_var):
        """
        Check if a variable with the given name is declared in the current or global scope.

        :param name_var: The name of the variable to check for declaration.
        :type name_var: str
        :return: True if the variable is declared in the current or global scope, False otherwise.
        :rtype: bool
        """
        for scope in reversed(self.scopes):
            if name_var in scope:
                return True
        return False

    def check_variable_declared(self, name_var):
        """
        Checks if a variable is declared and retrieves its declared type.

        :param name_var: The name of the variable to check.
        :type name_var: str
        :return: The declared type of the variable.
        :rtype: Any
        :raises SemanticException: If the variable is used without being declared.
        """
        if not self.is_variable_declared(name_var):
            raise SemanticException(f"Variable '{name_var}' is used without being declared.")
        else:
            return self.get_declared_type(name_var)

    def get_declared_type(self, name):
        """
        Retrieves the type of a declared variable or identifier from the symbol table.

        The function searches through the symbol table entries in reverse order to find
        the most recent declaration of the given name. If the identifier is found, its
        associated type is returned. If the identifier is not found in the symbol table,
        a ``SemanticException`` is raised.

        :param name: The name of the identifier to look for in the symbol table.
        :type name: str

        :return: The type of the identified variable or declaration.
        :rtype: Any

        :raises SemanticException: If the identifier is not found in the symbol table.
        """
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                return entry["type"]
        raise SemanticException(f"Identifier '{name}' not found in the symbol table.")

    def check_type(self, type1, type2):
        """
        Validates whether the two given types are compatible. If the types do
        not match, a SemanticException is raised to indicate an invalid operation.
        This function ensures type safety during runtime.

        :param type1: The first type to compare.
        :param type2: The second type to compare.
        :return: None
        :raises SemanticException: If the types do not match.
        """
        if type1 != type2:
            raise SemanticException(f"Type error: Operation between '{type1}' and '{type2}' is not allowed.")

    def get_variable_type(self, name):
        """
        Determine the type of a variable by searching through the current and parent
        scopes in reverse order. The method looks for the variable name in each scope
        and returns its type if found. If the variable is not declared in any of the
        scopes, an exception is raised.

        :param name: The name of the variable whose type is to be determined.
        :type name: str
        :return: The type of the variable as a string.
        :rtype: str
        :raises SemanticException: If the variable is not declared in any scope.
        """
        for scope in reversed(self.scopes):
            if name in scope and isinstance(scope[name], str):
                return scope[name]
        raise SemanticException(f"Variable '{name}' is not declared.")

    def init_variable(self, name, type_affect):
        """
        Marks a variable as initialized within the symbol table and verifies its type consistency.

        This function updates the initialization status of a variable if it is declared
        in the symbol table. Additionally, it ensures that the type of the variable matches
        the expected type. If the variable is not declared or the types do not match, it raises
        a `SemanticException`.

        :param name: The name of the variable to initialize.
        :type name: str
        :param type_affect: The type of the value to be assigned to the variable.
        :type type_affect: str
        :return: None
        :raises SemanticException: If the variable is not declared in the symbol table or if the
            type of the assigned value does not match the declared type.
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
        Checks if a variable with the given name has been initialized. If the
        variable is found in the symbol table but is not initialized, raises a
        SemanticException. Also raises a SemanticException if the variable is
        not declared in the symbol table.

        :param name: The name of the variable to check (str).
        :return: None
        :raises SemanticException: If the variable is not declared or not
            initialized in the symbol table.
        """
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                if not entry["initialized"]:
                    raise SemanticException(f"Variable '{name}' is used without being initialized.")
                return
        raise SemanticException(f"Variable '{name}' is not declared.")

    def check_condition_if(self, type_cond):
        """
        Checks whether the provided condition type is a boolean.

        This function ensures that a first-class requirement for
        an if-condition is being met, i.e., its type being boolean.
        If the condition is of an invalid type, a `SemanticException`
        will be raised, detailing the expected and received type.

        :param type_cond: The type of the if-condition to be verified.
        :type type_cond: str
        :raises SemanticException: If the type is not "boolean".
        """
        if type_cond != "boolean":
            raise SemanticException(f"Type error: The if-condition must be a boolean, got '{type_cond}'.")

    def check_condition_while(self, type_cond):
        """
        Validates the type of a condition used in a 'while' construct. The method checks
        if the provided condition type is "boolean". If the type is not "boolean", it
        raises a SemanticException with an appropriate error message.

        :param type_cond: The type of the condition to validate.
        :type type_cond: str
        :raises SemanticException: If the condition type is not "boolean".
        """
        if type_cond != "boolean":
            raise SemanticException(f"Type error: The while-condition must be a boolean, got '{type_cond}'.")


    def declare_function(self, name, params,type_return):
        """
        Declares a new function in the symbol table, enforcing uniqueness of function
        declarations by name within the same scope.

        :param name: The name of the function to be declared.
        :type name: str
        :param params: The parameters of the function, typically as a list or other
            iterable structure containing parameter specifications.
        :type params: Any
        :param type_return: The return type of the function being declared.
        :type type_return: Any
        :raises SemanticException: If a function with the same name has already been
            declared in the current scope.
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
        Declares a new procedure within the symbol table. The procedure, along with
        its name, type, scope, and parameters, is appended to the symbol table if it
        has not already been declared. If a procedure with the same name is already
        present, an error is raised.

        :param name: The name of the procedure to declare.
        :type name: str
        :param params: A list of parameters defining the procedure. Each parameter
                       is represented as a dictionary with details such as type and
                       name.
        :type params: list[dict]
        :raises SemanticException: If a procedure with the provided name has already
                                    been declared.
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
        Retrieves the parameters of a function or a procedure from the symbol table by its name.

        The method searches for the first occurrence of the function name in the
        symbol table, starting from the most recent entry and iterating backwards.
        If the function is found, its associated parameters are returned. If the
        function is not found, an exception is raised.

        :param name: Name of the function to retrieve parameters for
        :type name: str
        :return: Parameters of the specified function
        :rtype: Any
        :raises SemanticException: If the function name is not found in the symbol table
        """
        for entry in reversed(self.symbols):
            if entry["name"] == name:
                return entry["parameters"]
        raise SemanticException(f"Ident '{name}' not found in the symbol table.")
    def check_parameters(self,name,params):
        """
        Checks the validity of parameters passed for a function or procedure by comparing them
        against its declaration within the symbol table.

        This method ensures the provided parameters match both in count and type with what is
        declared for the function or procedure. Additionally, it identifies if the given name
        is either a function or a procedure and processes accordingly. An exception is raised
        if there is a mismatch or if the specified function or procedure cannot be found in the
        symbol table.

        :param name: The name of the function or procedure to check.
        :type name: str
        :param params: A list of parameters provided at the call site that are to be validated.
        :type params: list
        :return: The return type of the function if it is a function, or None if it is a procedure.
        :rtype: Optional[Any]
        :raises SemanticException: If there is a mismatch in parameter count or types, or if
            the specified function or procedure is not found.
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