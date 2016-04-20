# -*- coding: utf-8 -*-
"""
hpack
~~~~~

HTTP/2 header encoding for Python.
"""
from .hpack import Encoder, Decoder
from .struct import HeaderTuple, NeverIndexedHeaderTuple
from .exceptions import HPACKError, HPACKDecodingError, InvalidTableIndex

__all__ = [
    'Encoder', 'Decoder', 'HPACKError', 'HPACKDecodingError',
    'InvalidTableIndex', 'HeaderTuple', 'NeverIndexedHeaderTuple'
]

__version__ = '2.2.0'
