try:
    from .c_huffman import *
except ModuleNotFoundError:
    from .py_huffman import *
    