from __future__ import annotations

from hpack import HPACKDecodingError
from hpack.huffman import HuffmanEncoder
from hpack.huffman_constants import REQUEST_CODES, REQUEST_CODES_LENGTH
from hpack.huffman_table import decode_huffman

from concurrent.futures import ThreadPoolExecutor

import pytest

class TestHuffmanEncoderBenchmark:

    @pytest.mark.benchmark
    def test_request_huffman_encode(self):
        encoder = HuffmanEncoder(REQUEST_CODES, REQUEST_CODES_LENGTH)
        assert (
            encoder.encode(b"www.example.com") ==
            b'\xf1\xe3\xc2\xe5\xf2:k\xa0\xab\x90\xf4\xff'
        )
        assert encoder.encode(b"no-cache") == b'\xa8\xeb\x10d\x9c\xbf'
        assert encoder.encode(b"custom-key") == b'%\xa8I\xe9[\xa9}\x7f'
        assert (
            encoder.encode(b"custom-value") == b'%\xa8I\xe9[\xb8\xe8\xb4\xbf'
        )


    @pytest.mark.benchmark
    def test_request_huffman_encoder_under_heavy_threading(self):
        INPUTS = [
            b"www.example.com",
            b"no-cache",
            b"custom-key",
            b"custom-value"
        ] * 50 # 200 Entries to simulate heavy traffic

        ANSWERS = {
            b'\xf1\xe3\xc2\xe5\xf2:k\xa0\xab\x90\xf4\xff', 
            b'\xa8\xeb\x10d\x9c\xbf', 
            b'%\xa8I\xe9[\xa9}\x7f', 
            b'%\xa8I\xe9[\xb8\xe8\xb4\xbf'
        }
        encoder = HuffmanEncoder(REQUEST_CODES, REQUEST_CODES_LENGTH)
        
        with ThreadPoolExecutor(2) as te:
            for answer in te.map(encoder.encode, INPUTS):
                assert answer in ANSWERS




class TestHuffmanDecoderBenchmark:

    # 3.13t cannot use pytest-codspeed due to cffi-2.0 
    # so using markers was the best solution
    @pytest.mark.benchmark
    def test_request_huffman_decoder(self):
        assert (
        decode_huffman(b'\xf1\xe3\xc2\xe5\xf2:k\xa0\xab\x90\xf4\xff') ==
            b"www.example.com"
        )
        assert decode_huffman(b'\xa8\xeb\x10d\x9c\xbf') == b"no-cache"
        assert decode_huffman(b'%\xa8I\xe9[\xa9}\x7f') == b"custom-key"
        assert (
            decode_huffman(b'%\xa8I\xe9[\xb8\xe8\xb4\xbf') == b"custom-value"
        )

    @pytest.mark.benchmark
    def test_request_huffman_decoder_under_heavy_threading(self):
        # Trying to ensure that huffman decoder is threadsafe and can work under heavy traffic
        # SEE: https://github.com/python-hyper/hpack/issues/284
        INPUTS = [
            b'\xf1\xe3\xc2\xe5\xf2:k\xa0\xab\x90\xf4\xff', 
            b'\xa8\xeb\x10d\x9c\xbf', 
            b'%\xa8I\xe9[\xa9}\x7f', 
            b'%\xa8I\xe9[\xb8\xe8\xb4\xbf'
        ] * 50 # 200 entries should be enough to simulate heavy loads to rip through
        ANSWERS = {
            b"www.example.com",
            b"no-cache",
            b"custom-key",
            b"custom-value"
        }

        with ThreadPoolExecutor(2) as te:
            for answer in te.map(decode_huffman, INPUTS):
                assert answer in ANSWERS
    
