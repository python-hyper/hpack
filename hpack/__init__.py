# -*- coding: utf-8 -*-
"""
hpack
~~~~~

HTTP/2 header encoding for Python.
"""
from .hpack import Encoder, Decoder
from .exceptions import HPACKError, HPACKDecodingError

__version__ = '2.0.0'
