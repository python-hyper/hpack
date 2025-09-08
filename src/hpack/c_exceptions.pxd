cdef class HPACKError(Exception):
    pass 

cdef class HPACKDecodingError(HPACKError):
    pass

cdef class InvalidTableIndexError(HPACKDecodingError):
    pass 

cdef class InvalidTableIndex(InvalidTableIndexError):
    pass

cdef class OversizedHeaderListError(HPACKDecodingError):
    pass 

cdef class InvalidTableSizeError(HPACKDecodingError):
    pass
