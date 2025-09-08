cdef class HPACKError(Exception):
    """
    The base cdef class for all ``hpack`` exceptions.
    """



cdef class HPACKDecodingError(HPACKError):
    """
    An error has been encountered while performing HPACK decoding.
    """



cdef class InvalidTableIndexError(HPACKDecodingError):
    """
    An invalid table index was received.

    .. versionadded:: 4.1.0
    """

cdef class InvalidTableIndex(InvalidTableIndexError):  # noqa: N818
    """
    An invalid table index was received.

    .. deprecated:: 4.1.0
       Renamed to :class:`InvalidTableIndexError`, use it instead.
    """


cdef class OversizedHeaderListError(HPACKDecodingError):
    """
    A header list that was larger than we allow has been received. This may be
    a DoS attack.

    .. versionadded:: 2.3.0
    """


cdef class InvalidTableSizeError(HPACKDecodingError):
    """
    An attempt was made to change the decoder table size to a value larger than
    allowed, or the list was shrunk and the remote peer didn't shrink their
    table size.

    .. versionadded:: 3.0.0
    """
