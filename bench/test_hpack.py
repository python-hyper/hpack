import hpack.hpack


class TestHpackEncodingIntegersBenchmarks:
    def test_encode_small_integer_large_prefix(self, benchmark):
        benchmark(hpack.hpack.encode_integer, 120, 7)

    def test_encode_small_integer_small_prefix(self, benchmark):
        benchmark(hpack.hpack.encode_integer, 120, 1)

    def test_encode_large_integer_large_prefix(self, benchmark):
        benchmark(hpack.hpack.encode_integer, 120000, 7)

    def test_encode_large_integer_small_prefix(self, benchmark):
        benchmark(hpack.hpack.encode_integer, 120000, 1)


class TestHpackDecodingIntegersBenchmarks:
    def test_decode_small_integer_large_prefix(self, benchmark):
        data = hpack.hpack.encode_integer(120, 7)
        benchmark(hpack.hpack.decode_integer, data, 7)

    def test_decode_small_integer_small_prefix(self, benchmark):
        data = hpack.hpack.encode_integer(120, 1)
        benchmark(hpack.hpack.decode_integer, data, 1)

    def test_decode_large_integer_large_prefix(self, benchmark):
        data = hpack.hpack.encode_integer(120000, 7)
        benchmark(hpack.hpack.decode_integer, data, 7)

    def test_decode_large_integer_small_prefix(self, benchmark):
        data = hpack.hpack.encode_integer(120000, 1)
        benchmark(hpack.hpack.decode_integer, data, 1)
