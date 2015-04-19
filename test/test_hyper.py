# -*- coding: utf-8 -*-
from hpack.hpack import Encoder, Decoder, encode_integer, decode_integer
from hpack.huffman import HuffmanDecoder
from hpack.exceptions import HPACKDecodingError
import os
import pytest


class TestHuffmanDecoder(object):
    def test_huffman_decoder_throws_useful_exceptions(self):
        # Specify a HuffmanDecoder with no values in it, then attempt to decode
        # using it.
        d = HuffmanDecoder([], [])
        with pytest.raises(HPACKDecodingError):
            d.decode(b'test')


class TestHPACKEncoder(object):
    # These tests are stolen entirely from the IETF specification examples.
    def test_literal_header_field_with_indexing(self):
        """
        The header field representation uses a literal name and a literal
        value.
        """
        e = Encoder()
        header_set = {'custom-key': 'custom-header'}
        result = b'\x40\x0acustom-key\x0dcustom-header'

        assert e.encode(header_set, huffman=False) == result
        assert list(e.header_table) == [
            (n.encode('utf-8'), v.encode('utf-8')) for n, v in header_set.items()
        ]

    def test_indexed_literal_header_field_with_indexing(self):
        """
        The header field representation uses an indexed name and a literal
        value and performs incremental indexing.
        """
        e = Encoder()
        header_set = {':path': '/sample/path'}
        result = b'\x44\x0c/sample/path'

        assert e.encode(header_set, huffman=False) == result
        assert list(e.header_table) == [
            (n.encode('utf-8'), v.encode('utf-8')) for n, v in header_set.items()
        ]

    def test_indexed_header_field(self):
        """
        The header field representation uses an indexed header field, from
        the static table.
        """
        e = Encoder()
        header_set = {':method': 'GET'}
        result = b'\x82'

        assert e.encode(header_set, huffman=False) == result
        assert list(e.header_table) == []

    def test_indexed_header_field_from_static_table(self):
        e = Encoder()
        e.header_table_size = 0
        header_set = {':method': 'GET'}
        result = b'\x82'

        # Make sure we don't emit an encoding context update.
        e._table_size_changed = False

        assert e.encode(header_set, huffman=False) == result
        assert list(e.header_table) == []

    def test_request_examples_without_huffman(self):
        """
        This section shows several consecutive header sets, corresponding to
        HTTP requests, on the same connection.
        """
        e = Encoder()
        first_header_set = [
            (':method', 'GET',),
            (':scheme', 'http',),
            (':path', '/',),
            (':authority', 'www.example.com'),
        ]
        # We should have :authority in first_header_table since we index it
        first_header_table = [(':authority', 'www.example.com')]
        first_result = b'\x82\x86\x84\x41\x0fwww.example.com'

        assert e.encode(first_header_set, huffman=False) == first_result
        assert list(e.header_table) == [
            (n.encode('utf-8'), v.encode('utf-8')) for n, v in first_header_table
        ]

        second_header_set = [
            (':method', 'GET',),
            (':scheme', 'http',),
            (':path', '/',),
            (':authority', 'www.example.com',),
            ('cache-control', 'no-cache'),
        ]
        second_header_table = [
            ('cache-control', 'no-cache'),
            (':authority', 'www.example.com')
        ]
        second_result = b'\x82\x86\x84\xbeX\x08no-cache'

        assert e.encode(second_header_set, huffman=False) == second_result
        assert list(e.header_table) == [
            (n.encode('utf-8'), v.encode('utf-8')) for n, v in second_header_table
        ]

        third_header_set = [
            (':method', 'GET',),
            (':scheme', 'https',),
            (':path', '/index.html',),
            (':authority', 'www.example.com',),
            ('custom-key', 'custom-value'),
        ]
        third_result = (
            b'\x82\x87\x85\xbf@\ncustom-key\x0ccustom-value'
        )

        assert e.encode(third_header_set, huffman=False) == third_result
        # Don't check the header table here, it's just too complex to be
        # reliable. Check its length though.
        assert len(e.header_table) == 3

    def test_request_examples_with_huffman(self):
        """
        This section shows the same examples as the previous section, but
        using Huffman encoding for the literal values.
        """
        e = Encoder()
        first_header_set = [
            (':method', 'GET',),
            (':scheme', 'http',),
            (':path', '/',),
            (':authority', 'www.example.com'),
        ]
        first_header_table = [(':authority', 'www.example.com')]
        first_result = (
            b'\x82\x86\x84\x41\x8c\xf1\xe3\xc2\xe5\xf2:k\xa0\xab\x90\xf4\xff'
        )

        assert e.encode(first_header_set, huffman=True) == first_result
        assert list(e.header_table) == [
            (n.encode('utf-8'), v.encode('utf-8')) for n, v in first_header_table
        ]

        second_header_table = [
            ('cache-control', 'no-cache'),
            (':authority', 'www.example.com')
        ]
        second_header_set = [
            (':method', 'GET',),
            (':scheme', 'http',),
            (':path', '/',),
            (':authority', 'www.example.com',),
            ('cache-control', 'no-cache'),
        ]
        second_result = b'\x82\x86\x84\xbeX\x86\xa8\xeb\x10d\x9c\xbf'

        assert e.encode(second_header_set, huffman=True) == second_result
        assert list(e.header_table) == [
            (n.encode('utf-8'), v.encode('utf-8')) for n, v in second_header_table
        ]

        third_header_set = [
            (':method', 'GET',),
            (':scheme', 'https',),
            (':path', '/index.html',),
            (':authority', 'www.example.com',),
            ('custom-key', 'custom-value'),
        ]
        third_result = (
            b'\x82\x87\x85\xbf'
            b'@\x88%\xa8I\xe9[\xa9}\x7f\x89%\xa8I\xe9[\xb8\xe8\xb4\xbf'
        )

        assert e.encode(third_header_set, huffman=True) == third_result
        assert len(e.header_table) == 3

    # These tests are custom, for hyper.
    def test_resizing_header_table(self):
        # We need to encode a substantial number of headers, to populate the
        # header table.
        e = Encoder()
        header_set = [
            (':method', 'GET'),
            (':scheme', 'https'),
            (':path', '/some/path'),
            (':authority', 'www.example.com'),
            ('custom-key', 'custom-value'),
            ("user-agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:16.0) Gecko/20100101 Firefox/16.0"),
            ("accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
            ('X-Lukasa-Test', '88989'),
        ]
        e.encode(header_set, huffman=True)

        # Resize the header table to a size so small that nothing can be in it.
        e.header_table_size = 40
        assert len(e.header_table) == 0

    def test_resizing_header_table_sends_context_update(self):
        e = Encoder()

        # Resize the header table to a size so small that nothing can be in it.
        e.header_table_size = 40

        # Now, encode a header set. Just a small one, with a well-defined
        # output.
        header_set = [(':method', 'GET')]
        out = e.encode(header_set, huffman=True)

        assert out == b'?\t\x82'

    def test_setting_table_size_to_the_same_does_nothing(self):
        e = Encoder()

        # Set the header table size to the default.
        e.header_table_size = 4096

        # Now encode a header set. Just a small one, with a well-defined
        # output.
        header_set = [(':method', 'GET')]
        out = e.encode(header_set, huffman=True)

        assert out == b'\x82'

    def test_evicting_header_table_objects(self):
        e = Encoder()

        # Set the header table size large enough to include one header.
        e.header_table_size = 66
        header_set = [('a', 'b'), ('long-custom-header', 'longish value')]
        e.encode(header_set)

        assert len(e.header_table) == 1


class TestHPACKDecoder(object):
    # These tests are stolen entirely from the IETF specification examples.
    def test_literal_header_field_with_indexing(self):
        """
        The header field representation uses a literal name and a literal
        value.
        """
        d = Decoder()
        header_set = [('custom-key', 'custom-header')]
        data = b'\x40\x0acustom-key\x0dcustom-header'

        assert d.decode(data) == header_set
        assert list(d.header_table) == [
            (n.encode('utf-8'), v.encode('utf-8')) for n, v in header_set
        ]

    def test_literal_header_field_without_indexing(self):
        """
        The header field representation uses an indexed name and a literal
        value.
        """
        d = Decoder()
        header_set = [(':path', '/sample/path')]
        data = b'\x04\x0c/sample/path'

        assert d.decode(data) == header_set
        assert list(d.header_table) == []

    def test_indexed_header_field(self):
        """
        The header field representation uses an indexed header field, from
        the static table.
        """
        d = Decoder()
        header_set = [(':method', 'GET')]
        data = b'\x82'

        assert d.decode(data) == header_set
        assert list(d.header_table) == []

    def test_request_examples_without_huffman(self):
        """
        This section shows several consecutive header sets, corresponding to
        HTTP requests, on the same connection.
        """
        d = Decoder()
        first_header_set = [
            (':method', 'GET',),
            (':scheme', 'http',),
            (':path', '/',),
            (':authority', 'www.example.com'),
        ]
        # The first_header_table doesn't contain 'authority'
        first_data = b'\x82\x86\x84\x01\x0fwww.example.com'

        assert d.decode(first_data) == first_header_set
        assert list(d.header_table) == []

        # This request takes advantage of the differential encoding of header
        # sets.
        second_header_set = [
            (':method', 'GET',),
            (':scheme', 'http',),
            (':path', '/',),
            (':authority', 'www.example.com',),
            ('cache-control', 'no-cache'),
        ]
        second_data = (
            b'\x82\x86\x84\x01\x0fwww.example.com\x0f\t\x08no-cache'
        )

        assert d.decode(second_data) == second_header_set
        assert list(d.header_table) == []

        third_header_set = [
            (':method', 'GET',),
            (':scheme', 'https',),
            (':path', '/index.html',),
            (':authority', 'www.example.com',),
            ('custom-key', 'custom-value'),
        ]
        third_data = (
            b'\x82\x87\x85\x01\x0fwww.example.com@\ncustom-key\x0ccustom-value'
        )

        assert d.decode(third_data) == third_header_set
        # Don't check the header table here, it's just too complex to be
        # reliable. Check its length though.
        assert len(d.header_table) == 1

    def test_request_examples_with_huffman(self):
        """
        This section shows the same examples as the previous section, but
        using Huffman encoding for the literal values.
        """
        d = Decoder()

        first_header_set = [
            (':method', 'GET',),
            (':scheme', 'http',),
            (':path', '/',),
            (':authority', 'www.example.com'),
        ]
        first_header_table = first_header_set[::-1]
        first_data = (
            b'\x82\x86\x84\x01\x8c\xf1\xe3\xc2\xe5\xf2:k\xa0\xab\x90\xf4\xff'
        )

        assert d.decode(first_data) == first_header_set
        assert list(d.header_table) == []

        second_header_set = [
            (':method', 'GET',),
            (':scheme', 'http',),
            (':path', '/',),
            (':authority', 'www.example.com',),
            ('cache-control', 'no-cache'),
        ]
        second_data = (
            b'\x82\x86\x84\x01\x8c\xf1\xe3\xc2\xe5\xf2:k\xa0\xab\x90\xf4\xff'
            b'\x0f\t\x86\xa8\xeb\x10d\x9c\xbf'
        )

        assert d.decode(second_data) == second_header_set
        assert list(d.header_table) == []

        third_header_set = [
            (':method', 'GET',),
            (':scheme', 'https',),
            (':path', '/index.html',),
            (':authority', 'www.example.com',),
            ('custom-key', 'custom-value'),
        ]
        third_data = (
            b'\x82\x87\x85\x01\x8c\xf1\xe3\xc2\xe5\xf2:k\xa0\xab\x90\xf4\xff@'
            b'\x88%\xa8I\xe9[\xa9}\x7f\x89%\xa8I\xe9[\xb8\xe8\xb4\xbf'
        )

        assert d.decode(third_data) == third_header_set
        assert len(d.header_table) == 1

    # These tests are custom, for hyper.
    def test_resizing_header_table(self):
        # We need to decode a substantial number of headers, to populate the
        # header table. This string isn't magic: it's the output from the
        # equivalent test for the Encoder.
        d = Decoder()
        data = (
            b'\x82\x88F\x87\x087A\x07"9\xffC\x8b\xdbm\x88>h\xd1\xcb\x12%' +
            b'\xba\x7f\x00\x88N\xb0\x8bt\x97\x90\xfa\x7f\x89N\xb0\x8bt\x97\x9a' +
            b'\x17\xa8\xff|\xbe\xefo\xaa\x96\xb4\x05\x04/G\xfa\xefBT\xc8\xb6' +
            b'\x19\xf5t|\x19\x11_Gz\x13\xd1\xf4\xf0\xe8\xfd\xf4\x18\xa4\xaf' +
            b'\xab\xa1\xfc\xfd\x86\xa4\x85\xff}\x1e\xe1O&\x81\xcab\x94\xc57G' +
            b'\x05<qo\x98\x1a\x92\x17U\xaf\x88\xf9\xc43\x8e\x8b\xe9C\x9c\xb5' +
            b'%\x11SX\x1ey\xc7E\xff\xcf=\x17\xd2\x879jJ"\xa6\xb0<\xf4_W\x95' +
            b'\xa5%\x9d?\xd0\x7f]^V\x94\x95\xff\x00\x8a\xfd\xcb\xf2\xd7\x92 ' +
            b'\x89|F\x11\x84\xae\xbb+\xb3'
        )
        d.decode(data)

        # Resize the header table to a size so small that nothing can be in it.
        d.header_table_size = 40
        assert len(d.header_table) == 0

    def test_apache_trafficserver(self):
        # This test reproduces the bug in #110, using exactly the same header
        # data.
        d = Decoder()
        data = (
            b'\x10\x07:status\x03200@\x06server\tATS/6.0.0'
            b'@\x04date\x1dTue, 31 Mar 2015 08:09:51 GMT'
            b'@\x0ccontent-type\ttext/html@\x0econtent-length\x0542468'
            b'@\rlast-modified\x1dTue, 31 Mar 2015 01:55:51 GMT'
            b'@\x04vary\x0fAccept-Encoding@\x04etag\x0f"5519fea7-a5e4"'
            b'@\x08x-served\x05Nginx@\x14x-subdomain-tryfiles\x04True'
            b'@\x07x-deity\thydra-lts@\raccept-ranges\x05bytes@\x03age\x010'
            b'@\x19strict-transport-security\rmax-age=86400'
            b'@\x03via2https/1.1 ATS (ApacheTrafficServer/6.0.0 [cSsNfU])'
        )
        expect = [
            (':status', '200'),
            ('server', 'ATS/6.0.0'),
            ('date', 'Tue, 31 Mar 2015 08:09:51 GMT'),
            ('content-type', 'text/html'),
            ('content-length', '42468'),
            ('last-modified', 'Tue, 31 Mar 2015 01:55:51 GMT'),
            ('vary', 'Accept-Encoding'),
            ('etag', '"5519fea7-a5e4"'),
            ('x-served', 'Nginx'),
            ('x-subdomain-tryfiles', 'True'),
            ('x-deity', 'hydra-lts'),
            ('accept-ranges', 'bytes'),
            ('age', '0'),
            ('strict-transport-security', 'max-age=86400'),
            ('via', 'https/1.1 ATS (ApacheTrafficServer/6.0.0 [cSsNfU])'),
        ]

        result = d.decode(data)

        assert result == expect
        # The status header shouldn't be indexed.
        assert len(d.header_table) == len(expect) - 1


class TestIntegerEncoding(object):
    # These tests are stolen from the HPACK spec.
    def test_encoding_10_with_5_bit_prefix(self):
        val = encode_integer(10, 5)
        assert len(val) == 1
        assert val == bytearray(b'\x0a')

    def test_encoding_1337_with_5_bit_prefix(self):
        val = encode_integer(1337, 5)
        assert len(val) == 3
        assert val == bytearray(b'\x1f\x9a\x0a')

    def test_encoding_42_with_8_bit_prefix(self):
        val = encode_integer(42, 8)
        assert len(val) == 1
        assert val == bytearray(b'\x2a')


class TestIntegerDecoding(object):
    # These tests are stolen from the HPACK spec.
    def test_decoding_10_with_5_bit_prefix(self):
        val = decode_integer(b'\x0a', 5)
        assert val == (10, 1)

    def test_encoding_1337_with_5_bit_prefix(self):
        val = decode_integer(b'\x1f\x9a\x0a', 5)
        assert val == (1337, 3)

    def test_encoding_42_with_8_bit_prefix(self):
        val = decode_integer(b'\x2a', 8)
        assert val == (42, 1)


class TestUtilities(object):
    def test_nghttp2_installs_correctly(self):
        # This test is a debugging tool: if nghttp2 is being tested by Travis,
        # we need to confirm it imports correctly. Hyper will normally hide the
        # import failure, so let's discover it here.
        # Alternatively, if we are *not* testing with nghttp2, this test should
        # confirm that it's not available.
        if os.environ.get('NGHTTP2'):
            import nghttp2
        else:
            with pytest.raises(ImportError):
                import nghttp2

        assert True
