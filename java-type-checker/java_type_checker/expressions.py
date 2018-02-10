# -*- coding: utf-8 -*-

from .types import Type


class Expression(object):
    """
    AST for simple Java expressions. Note that this package deal only with compile-time types;
    this class does not actually _evaluate_ expressions.
    """

    def static_type(self):
        """
        Returns the compile-time type of this expression, i.e. the most specific type that describes
        all the possible values it could take on at runtime. Subclasses must implement this method.
        """
        raise NotImplementedError(type(self).__name__ + " must implement static_type()")

    def check_types(self):
        """
        Validates the structure of this expression, checking for any logical inconsistencies in the
        child nodes and the operation this expression applies to them.
        """

        raise NotImplementedError(type(self).__name__ + " must implement check_types()")


class Variable(Expression):
    """ An expression that reads the value of a variable, e.g. `x` in the expression `x + 5`.
    """
    def __init__(self, name, declared_type):
        self.name = name                    #: The name of the variable
        self.declared_type = declared_type  #: The declared type of the variable (Type)

    def static_type(self):
        return self.declared_type

    def check_types(self):
        pass


class Literal(Expression):
    """ A literal value entered in the code, e.g. `5` in the expression `x + 5`.
    """
    def __init__(self, value, type):
        self.value = value  #: The literal value, as a string
        self.type = type    #: The type of the literal (Type)

    def static_type(self):
        return self.type

    def check_types(self):
        pass

class NullLiteral(Literal):
    def __init__(self):
        super().__init__("null", Type.null)

    def static_type(self):
        return Type.null



class MethodCall(Expression):
    """
    A Java method invocation, i.e. `foo.bar(0, 1, 2)`.
    """
    def __init__(self, receiver, method_name, *args):
        self.receiver = receiver        #: The object whose method we are calling (Expression)
        self.method_name = method_name  #: The name of the method to call (String)
        self.args = args                #: The method arguments (list of Expressions)

    def static_type(self):
        objType = self.receiver.static_type()
        method = objType.method_named(self.method_name)
        return method.return_type

    def check_types(self):
        primitives = [Type.int, Type.boolean, Type.double]
        objType = self.receiver.static_type()
        passedArgTypes = []

        if objType in primitives:           #cant call methods on primitives
            raise JavaTypeError("Type {0} does not have methods".format(
                objType.name
            ))

        if objType.method_named(self.method_name):          #if the object has the correct method
            method = objType.method_named(self.method_name)
            pass
        else:
            raise JavaTypeError("{0} has no method named {1}".format(
                objType.name,
                self.method_name
            ))

        if len(self.args) == len(method.argument_types):        #if you passed enough arguments for the method
            pass
        else:
            raise JavaTypeError("Wrong number of arguments for {0}: expected {1}, got {2}".format(
                                objType.name + "." + method.name+ "()",
                                len(method.argument_types),
                                len(self.args)))

        for e in self.args:
            passedArgTypes.append(e.static_type())
        for i in range(0,len(self.args)):                   # if you passed args of the correct type for the method
            if passedArgTypes[i] == method.argument_types[i]:
                self.args[i].check_types()
            elif method.argument_types[i] in passedArgTypes[i].direct_supertypes or passedArgTypes[i] == Type.null:
                self.args[i].check_types()
            else:
                raise JavaTypeError("{0} expects arguments of type {1}, but got {2}".format(
                                objType.name + "." + method.name + "()",
                                names(method.argument_types),
                                names(passedArgTypes)))


class ConstructorCall(Expression):
    """
    A Java object instantiation, i.e. `new Foo(0, 1, 2)`.
    """
    def __init__(self, instantiated_type, *args):
        self.instantiated_type = instantiated_type  #: The type to instantiate (Type)
        self.args = args                            #: Constructor arguments (list of Expressions)

    def static_type(self):
        return self.instantiated_type

    def check_types(self):
        # can't instantiate primitives
        primitives = [Type.int, Type.boolean, Type.double]
        if self.instantiated_type in primitives:
            raise JavaTypeError("Type {0} is not instantiable".format(
                self.instantiated_type.name
            ))
        if self.instantiated_type == Type.null:
            raise JavaTypeError("Type null is not instantiable")

        passedArgTypes = []     #setup a list for the types of passed arguments
        expectedArgTypes = self.instantiated_type.constructor.argument_types
        # make sure you passed the expected number of arguments
        if len(self.args) == len(expectedArgTypes):
            pass
        else:
            raise JavaTypeError("Wrong number of arguments for {0}: expected {1}, got {2}".format(
                                self.instantiated_type.name + " constructor",
                                len(expectedArgTypes),
                                len(self.args)))

        # make sure you passed arguments with the expected types (or supertypes)
        for e in self.args:
            passedArgTypes.append(e.static_type())
        for i in range(0,len(self.args)):
            if passedArgTypes[i] == expectedArgTypes[i]:
                self.args[i].check_types()
            elif expectedArgTypes[i] in passedArgTypes[i].direct_supertypes:
                self.args[i].check_types()
            elif passedArgTypes[i] == Type.null and not expectedArgTypes[i] in primitives:
                pass
            else:
                raise JavaTypeError("{0} expects arguments of type {1}, but got {2}".format(
                                self.instantiated_type.name + " constructor",
                                names(expectedArgTypes),
                                names(passedArgTypes)))


class JavaTypeError(Exception):
    """ Indicates a compile-time type error in an expression.
    """
    pass


def names(named_things):
    """ Helper for formatting pretty error messages
    """
    return "(" + ", ".join([e.name for e in named_things]) + ")"
