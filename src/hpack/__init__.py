"""
hpack
~~~~~

HTTP/2 header encoding for Python.
"""
from .hpack import Encoder, Decoder
from .struct import HeaderTuple, NeverIndexedHeaderTuple
from .exceptions import (
    HPACKError,
    HPACKDecodingError,
    InvalidTableIndex,
    OversizedHeaderListError,
    InvalidTableSizeError
)

__all__ = [
    'Encoder',
    'Decoder',
    'HeaderTuple',
    'NeverIndexedHeaderTuple',
    'HPACKError',
    'HPACKDecodingError',
    'InvalidTableIndex',
    'OversizedHeaderListError',
    'InvalidTableSizeError',
]

__version__ = '4.1.0+dev'
