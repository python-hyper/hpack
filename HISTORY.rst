Release History
===============

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
