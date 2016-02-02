Release History
===============

2.1.0 (2016-02-02)
------------------

**API Changes (Backward Compatible)**

- Added new ``InvalidTableIndex`` exception, a subclass of
  ``HPACKDecodingError``.
- Instead of throwing ``IndexError`` when encountering invalid encoded integers
  HPACK now throws ``HPACKDecodingError``.
- Instead of throwing ``UnicodeDecodeError`` when encountering headers that are
  not UTF-8 encoded, HPACK now throws ``HPACKDecodingError``.
- Instead of throwing ``IndexError`` when encountering invalid table offsets,
  HPACK now throws ``InvalidTableIndex``.
- Added ``raw`` flag to ``decode``, allowing ``decode`` to return bytes instead
  of attempting to decode the headers as UTF-8.

**Bugfixes**

- ``memoryview`` objects are now used when decoding HPACK, improving the
  performance by avoiding unnecessary data copies.

2.0.1 (2015-11-09)
------------------

- Fixed a bug where the Python HPACK implementation would only emit header
  table size changes for the total change between one header block and another,
  rather than for the entire sequence of changes.

2.0.0 (2015-10-12)
------------------

- Remove unused ``HPACKEncodingError``.
- Add the shortcut ability to import the public API (``Encoder``, ``Decoder``,
  ``HPACKError``, ``HPACKDecodingError``) directly, rather than from
  ``hpack.hpack``.

1.1.0 (2015-07-07)
------------------

- Add support for emitting 'never indexed' header fields, by using an optional
  third element in the header tuple. With thanks to @jimcarreer!

1.0.1 (2015-04-19)
------------------

- Header fields that have names matching header table entries are now added to
  the header table. This improves compression efficiency at the cost of
  slightly more table operations. With thanks to `Tatsuhiro Tsujikawa`_.

.. _Tatsuhiro Tsujikawa: https://github.com/tatsuhiro-t

1.0.0 (2015-04-13)
------------------

- Initial fork of the code from `hyper`_.

.. _hyper: https://hyper.readthedocs.org/
