# -*- coding: utf-8 -*-
# flake8: noqa
from collections import deque
import logging

from .exceptions import InvalidTableIndex

log = logging.getLogger(__name__)


def table_entry_size(name, value):
    """
    Calculates the size of a single entry

    This size is mostly irrelevant to us and defined
    specifically to accommodate memory management for
    lower level implementations. The 32 extra bytes are
    considered the "maximum" overhead that would be
    required to represent each entry in the table.

    See RFC7541 Section 4.1
    """
    return 32 + len(name) + len(value)


class HeaderTable(object):
    """
    Implements the combined static and dynamic header table

    The name and value arguments for all the functions
    should ONLY be byte strings (b'') however this is not
    strictly enforced in the interface.

    See RFC7541 Section 2.3
    """
    #: Default maximum size of the dynamic table. See
    #:  RFC7540 Section 6.5.2.
    DEFAULT_SIZE = 4096

    #: Constant list of static headers. See RFC7541 Section
    #:  2.3.1 and Appendix A
    STATIC_TABLE = (
        (b':authority'                  , b''             ),  # noqa
        (b':method'                     , b'GET'          ),  # noqa
        (b':method'                     , b'POST'         ),  # noqa
        (b':path'                       , b'/'            ),  # noqa
        (b':path'                       , b'/index.html'  ),  # noqa
        (b':scheme'                     , b'http'         ),  # noqa
        (b':scheme'                     , b'https'        ),  # noqa
        (b':status'                     , b'200'          ),  # noqa
        (b':status'                     , b'204'          ),  # noqa
        (b':status'                     , b'206'          ),  # noqa
        (b':status'                     , b'304'          ),  # noqa
        (b':status'                     , b'400'          ),  # noqa
        (b':status'                     , b'404'          ),  # noqa
        (b':status'                     , b'500'          ),  # noqa
        (b'Accept-Charset'              , b''             ),  # noqa
        (b'Accept-Encoding'             , b'gzip, deflate'),  # noqa
        (b'Accept-Language'             , b''             ),  # noqa
        (b'Accept-Ranges'               , b''             ),  # noqa
        (b'Accept'                      , b''             ),  # noqa
        (b'Access-Control-Allow-Origin' , b''             ),  # noqa
        (b'Age'                         , b''             ),  # noqa
        (b'Allow'                       , b''             ),  # noqa
        (b'Authorization'               , b''             ),  # noqa
        (b'Cache-Control'               , b''             ),  # noqa
        (b'Content-Disposition'         , b''             ),  # noqa
        (b'Content-Encoding'            , b''             ),  # noqa
        (b'Content-Language'            , b''             ),  # noqa
        (b'Content-Length'              , b''             ),  # noqa
        (b'Content-Location'            , b''             ),  # noqa
        (b'Content-Range'               , b''             ),  # noqa
        (b'Content-Type'                , b''             ),  # noqa
        (b'Cookie'                      , b''             ),  # noqa
        (b'Date'                        , b''             ),  # noqa
        (b'Etag'                        , b''             ),  # noqa
        (b'Expect'                      , b''             ),  # noqa
        (b'Expires'                     , b''             ),  # noqa
        (b'From'                        , b''             ),  # noqa
        (b'Host'                        , b''             ),  # noqa
        (b'If-Match'                    , b''             ),  # noqa
        (b'If-Modified-Since'           , b''             ),  # noqa
        (b'If-None-Match'               , b''             ),  # noqa
        (b'If-Range'                    , b''             ),  # noqa
        (b'If-Unmodified-Since'         , b''             ),  # noqa
        (b'Last-Modified'               , b''             ),  # noqa
        (b'Link'                        , b''             ),  # noqa
        (b'Location'                    , b''             ),  # noqa
        (b'Max-Forwards'                , b''             ),  # noqa
        (b'Proxy-Authenticate'          , b''             ),  # noqa
        (b'Proxy-Authorization'         , b''             ),  # noqa
        (b'Range'                       , b''             ),  # noqa
        (b'Referer'                     , b''             ),  # noqa
        (b'Refresh'                     , b''             ),  # noqa
        (b'Retry-After'                 , b''             ),  # noqa
        (b'Server'                      , b''             ),  # noqa
        (b'Set-Cookie'                  , b''             ),  # noqa
        (b'Strict-Transport-Security'   , b''             ),  # noqa
        (b'Transfer-Encoding'           , b''             ),  # noqa
        (b'User-Agent'                  , b''             ),  # noqa
        (b'Vary'                        , b''             ),  # noqa
        (b'Via'                         , b''             ),  # noqa
        (b'Www-Authenticate'            , b''             ),  # noqa
    )  # noqa

    STATIC_TABLE_LENGTH = len(STATIC_TABLE)

    def __init__(self):
        self._maxsize = HeaderTable.DEFAULT_SIZE
        self._current_size = 0
        self.resized = False
        self.dynamic_entries = deque()

    def get_by_index(self, index):
        """
        Returns the entry specified by index

        Note that the table is 1-based ie an index of 0 is
        invalid.  This is due to the fact that a zero value
        index signals that a completely unindexed header
        follows.

        The entry will either be from the static table or
        the dynamic table depending on the value of index.
        """
        index -= 1
        if 0 <= index and index < HeaderTable.STATIC_TABLE_LENGTH:
            return HeaderTable.STATIC_TABLE[index]

        index -= HeaderTable.STATIC_TABLE_LENGTH
        if index < len(self.dynamic_entries):
            return self.dynamic_entries[index]

        raise InvalidTableIndex("Invalid table index %d" % index)

    def __repr__(self):
        return "HeaderTable(%d, %s, %r)" % (
            self._maxsize,
            self.resized,
            self.dynamic_entries
        )

    def add(self, name, value):
        """
        Adds a new entry to the table

        We reduce the table size if the entry will make the
        table size greater than maxsize.
        """
        # We just clear the table if the entry is too big
        size = table_entry_size(name, value)
        if size > self._maxsize:
            self.dynamic_entries.clear()
            self._current_size = 0
        else:
            # Add new entry
            self.dynamic_entries.appendleft((name, value))
            self._current_size += size
            self._shrink()

    def search(self, name, value):
        """
        Searches the table for the entry specified by name
        and value

        Returns one of the following:
            - ``None``, no match at all
            - ``(index, name, None)`` for partial matches on name only.
            - ``(index, name, value)`` for perfect matches.
        """
        offset = HeaderTable.STATIC_TABLE_LENGTH + 1
        partial = None
        for (i, (n, v)) in enumerate(HeaderTable.STATIC_TABLE):
            if n == name:
                if v == value:
                    return i + 1, n, v
                elif partial is None:
                    partial = (i + 1, n, None)
        for (i, (n, v)) in enumerate(self.dynamic_entries):
            if n == name:
                if v == value:
                    return i + offset, n, v
                elif partial is None:
                    partial = (i + offset, n, None)
        return partial

    @property
    def maxsize(self):
        return self._maxsize

    @maxsize.setter
    def maxsize(self, newmax):
        newmax = int(newmax)
        log.debug("Resizing header table to %d from %d", newmax, self._maxsize)
        oldmax = self._maxsize
        self._maxsize = newmax
        self.resized = (newmax != oldmax)
        if newmax <= 0:
            self.dynamic_entries.clear()
            self._current_size = 0
        elif oldmax > newmax:
            self._shrink()

    def _shrink(self):
        """
        Shrinks the dynamic table to be at or below maxsize
        """
        cursize = self._current_size
        while cursize > self._maxsize:
            name, value = self.dynamic_entries.pop()
            cursize -= table_entry_size(name, value)
            log.debug("Evicting %s: %s from the header table", name, value)
        self._current_size = cursize
