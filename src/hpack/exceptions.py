try:
    from .c_exceptions import *
except ModuleNotFoundError:
    from .py_exceptions import *
