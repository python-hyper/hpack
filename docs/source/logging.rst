Logging configuration
=====================

``hpack`` uses Python's standard :mod:`logging` package and creates named
loggers for its modules. The most verbose encoder, decoder, and header table
diagnostics are emitted by the ``hpack.hpack`` and ``hpack.table`` loggers at
``DEBUG`` level.

If your application enables ``DEBUG`` logging globally but does not need these
low-level HPACK diagnostics, configure the ``hpack`` logger separately:

.. code-block:: python

    import logging

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("hpack").setLevel(logging.WARNING)

This leaves ``DEBUG`` logging enabled for your application while suppressing
debug records from ``hpack`` and its child loggers.

You can also configure the individual modules if you need finer control:

.. code-block:: python

    import logging

    logging.getLogger("hpack.hpack").setLevel(logging.WARNING)
    logging.getLogger("hpack.table").setLevel(logging.WARNING)
