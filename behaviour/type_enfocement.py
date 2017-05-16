import functools
import collections

def accepts(argtypes, kwargtypes):

    if type(argtypes) is not list:
        raise SyntaxError("'accepts' decorator accepts argtypes only as list")
    if type(kwargtypes) is not dict:
        raise SyntaxError("'accepts' decorator accepts kwargtypes only as dict")

    def accepts_wraper(func):
        @functools.wraps(func)
        def acceptor(*args, **kwargs):
            for i, arg, argt in zip(range(len(args)), args, argtypes):
                if type(arg) is not argt:
                    raise TypeError("Function '{}' expects argument #{} of type '{}', got '{}' instead".format(
                                    func.__name__, i, argt.__name__, type(arg).__name__))
            for key, val in kwargs.items():
                if key in kwargtypes:
                    if type(val) is not kwargtypes[key]:
                        raise TypeError("Function '{}' expects argument '{}' of type '{}', got '{}' instead".format(
                                        func.__name__, key, kwargtypes[key].__name__, type(val).__name__))
            return func(*args, **kwargs)
        acceptor.__argtypes = argtypes
        acceptor.__kwargtypes = kwargtypes
        return acceptor
    return accepts_wraper


def returns(rettype):

    def returns_wraper(func):
        @functools.wraps(func)
        def returner(*args, **kwargs):
            retval = func(*args, **kwargs)
            if type(retval) is not rettype:
                raise TypeError("Function '{}' expected to return type '{}', got '{}' instead".format(
                                func.__name__, type(rettype).__name__, type(retval).__name__))
            return retval
        returner.__returns = rettype
        return returner
    return returns_wraper


def enforce_kwargs(possible_kwargs):
    if type(possible_kwargs) is not set:
        if isinstance(possible_kwargs, collections.Iterable):
            possible_kwargs = set(possible_kwargs)
        else:
            raise SyntaxError("possible_kwargs should be iterable")
    if any([type(kwn) is not str for kwn in possible_kwargs]):
        raise SyntaxError("possible_kwargs should be strings")

    def enforce_kwargs_wraper(func):
        @functools.wraps(func)
        def enforcer(*args, **kwargs):
            kw_names = set(kwargs.keys())
            difference = kw_names.difference(possible_kwargs)
            if difference:
                raise RuntimeError("Unexpected kwargs passed to '{}': {}".format(func.__name__, str(difference)))
            return func(*args, **kwargs)
        return enforcer
    return enforce_kwargs_wraper


if __name__ == "__main__":
    @accepts([list, int], {"x": int, "l" : list, "f" : float })
    def foo(l, x=0, **kwargs):
        print("foo")

    foo([1, 2, 3], 1, f=3.14)
    foo(f=3.14, l=[1, 2, 3], x=1)

    try:
        foo(None)
    except TypeError as te:
        print("Expected type error: {}".format(str(te)))

    try:
        foo([], x=None)
    except TypeError as te:
        print("Expected type error: {}".format(str(te)))

    @returns(int)
    def bar():
        return 1

    print("Expected print: {}".format(bar()))

    @returns(int)
    def baz():
        return None

    try:
        baz()
    except TypeError as te:
        print("Expected type error: {}".format(str(te)))

    @enforce_kwargs(["testkw"])
    def pschooo(**kwargs):
        print("PSCHOOO")

    pschooo()
    pschooo(testkw="testkw")

    try:
        pschooo(unknownname="unknownname")
    except RuntimeError as e:
        print("Expected RuntimeError: {}".format(str(e)))


