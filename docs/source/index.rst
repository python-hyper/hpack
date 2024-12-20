hpack: Pure-Python HTTP/2 Header Encoding
=========================================

hpack provides a simple Python interface to the `HPACK`_ compression algorithm,
used to encode HTTP headers in HTTP/2. Used by some of the most popular
HTTP/2 implementations in Python, the hpack library offers a great and simple
Python interface without any dependencies, strictly confirming to `RFC 7541`_..

Using hpack is easy:

.. code-block:: python

    from hpack import Encoder, Decoder

    headers = [
        (':method', 'GET'),
        (':path', '/jimiscool/'),
        ('X-Some-Header', 'some_value'),
    ]

    e = Encoder()
    encoded_bytes = e.encode(headers)

    d = Decoder()
    decoded_headers = d.decode(encoded_bytes)


Contents
--------

.. toctree::
   :maxdepth: 2

   installation
   api
   security/index


.. _HPACK: https://tools.ietf.org/html/rfc7541
.. _RFC 7541: https://tools.ietf.org/html/rfc7541
