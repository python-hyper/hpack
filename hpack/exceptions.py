# -*- coding: utf-8 -*-
"""
hyper/http20/exceptions
~~~~~~~~~~~~~~~~~~~~~~~

This defines exceptions used in the HTTP/2 portion of hyper.
"""


class HPACKError(Exception):
    """
    The base class for all ``hpack`` exceptions.
    """
    pass


class HPACKDecodingError(HPACKError):
    """
    An error has been encountered while performing HPACK decoding.
    """
    pass
