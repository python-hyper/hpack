try:
    from .c_table import *
except ModuleNotFoundError:
    from .py_table import *
    