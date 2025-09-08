

cdef class HuffmanEncoder:
    """
    Encodes a string according to the Huffman encoding table defined in the
    HPACK specification.
    """
    cdef:
        list huffman_code_list
        list huffman_code_list_lengths

    cpdef bytes encode(self, bytes bytes_to_encode)
