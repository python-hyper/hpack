"""
An implementation of a bitwise prefix tree specially built for decoding
Huffman-coded content where we already know the Huffman table.
"""
from __future__ import annotations


class HuffmanEncoder:
    """
    Encodes a string according to the Huffman encoding table defined in the
    HPACK specification.
    """

    def __init__(self, huffman_code_list: list[int], huffman_code_list_lengths: list[int]) -> None:
        self.huffman_code_list = huffman_code_list
        self.huffman_code_list_lengths = huffman_code_list_lengths

    def encode(self, bytes_to_encode: bytes | None) -> bytes:
        """
        Given a string of bytes, encodes them according to the HPACK Huffman
        specification.
        """
        # If handed the empty string, just immediately return.
        if not bytes_to_encode:
            return b""

        # For longer byte strings, assemble the bits in C instead of repeatedly
        # shifting an ever-growing Python integer. Build the symbol map for this
        # call so changes to caller-owned coding tables are always observed.
        if type(bytes_to_encode) is bytes and len(bytes_to_encode) >= 256 and type(self) is HuffmanEncoder:
            codes = self.huffman_code_list
            lengths = self.huffman_code_list_lengths
            if type(codes) is list and type(lengths) is list and len(codes) >= 256 and len(lengths) >= 256:
                symbols = {}
                for symbol in set(bytes_to_encode):
                    code, length = codes[symbol], lengths[symbol]
                    if type(code) is not int or type(length) is not int or not 1 <= length <= 30 or not 0 <= code < (1 << length):
                        break
                    symbols[symbol] = f"{code:0{length}b}"
                else:
                    bits = "".join(map(symbols.__getitem__, bytes_to_encode))
                    bits += "1" * (-len(bits) % 8)
                    return int(bits, 2).to_bytes(len(bits) // 8, "big")

        final_num = 0
        final_int_len = 0

        # Turn each byte into its huffman code. These codes aren't necessarily
        # octet aligned, so keep track of how far through an octet we are. To
        # handle this cleanly, just use a single giant integer.
        for byte in bytes_to_encode:
            bin_int_len = self.huffman_code_list_lengths[byte]
            bin_int = self.huffman_code_list[byte] & (
                2 ** (bin_int_len + 1) - 1
            )
            final_num <<= bin_int_len
            final_num |= bin_int
            final_int_len += bin_int_len

        # Pad out to an octet with ones.
        bits_to_be_padded = (8 - (final_int_len % 8)) % 8
        final_num <<= bits_to_be_padded
        final_num |= (1 << bits_to_be_padded) - 1

        # Convert the number to hex without leading '0x' or trailing 'L'.
        s = f"{final_num:x}"

        # If this is odd, prepend a zero.
        s = "0" + s if len(s) % 2 != 0 else s

        # This number should have twice as many digits as bytes. If not, we're
        # missing some leading zeroes. Work out how many bytes we want and how
        # many digits we have, then add the missing zero digits to the front.
        total_bytes = (final_int_len + bits_to_be_padded) // 8
        expected_digits = total_bytes * 2

        if len(s) != expected_digits:
            missing_digits = expected_digits - len(s)
            s = ("0" * missing_digits) + s

        return bytes.fromhex(s)
