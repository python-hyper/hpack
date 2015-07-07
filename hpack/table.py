from collections import deque
import logging

log = logging.getLogger(__name__)


def table_entry_size(name, value):
    """
    Calculates the size of a single entry

    This size is mostly irrelevant to us and defined
    specifically to accommodate memory management for
    lower level implementions. The 32 extra bytes are
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
        (b':authority'                  , b''             ),
        (b':method'                     , b'GET'          ),
        (b':method'                     , b'POST'         ),
        (b':path'                       , b'/'            ),
        (b':path'                       , b'/index.html'  ),
        (b':scheme'                     , b'http'         ),
        (b':scheme'                     , b'https'        ),
        (b':status'                     , b'200'          ),
        (b':status'                     , b'204'          ),
        (b':status'                     , b'206'          ),
        (b':status'                     , b'304'          ),
        (b':status'                     , b'400'          ),
        (b':status'                     , b'404'          ),
        (b':status'                     , b'500'          ),
        (b'accept-charset'              , b''             ),
        (b'accept-encoding'             , b'gzip, deflate'),
        (b'accept-language'             , b''             ),
        (b'accept-ranges'               , b''             ),
        (b'accept'                      , b''             ),
        (b'access-control-allow-origin' , b''             ),
        (b'age'                         , b''             ),
        (b'allow'                       , b''             ),
        (b'authorization'               , b''             ),
        (b'cache-control'               , b''             ),
        (b'content-disposition'         , b''             ),
        (b'content-encoding'            , b''             ),
        (b'content-language'            , b''             ),
        (b'content-length'              , b''             ),
        (b'content-location'            , b''             ),
        (b'content-range'               , b''             ),
        (b'content-type'                , b''             ),
        (b'cookie'                      , b''             ),
        (b'date'                        , b''             ),
        (b'etag'                        , b''             ),
        (b'expect'                      , b''             ),
        (b'expires'                     , b''             ),
        (b'from'                        , b''             ),
        (b'host'                        , b''             ),
        (b'if-match'                    , b''             ),
        (b'if-modified-since'           , b''             ),
        (b'if-none-match'               , b''             ),
        (b'if-range'                    , b''             ),
        (b'if-unmodified-since'         , b''             ),
        (b'last-modified'               , b''             ),
        (b'link'                        , b''             ),
        (b'location'                    , b''             ),
        (b'max-forwards'                , b''             ),
        (b'proxy-authenticate'          , b''             ),
        (b'proxy-authorization'         , b''             ),
        (b'range'                       , b''             ),
        (b'referer'                     , b''             ),
        (b'refresh'                     , b''             ),
        (b'retry-after'                 , b''             ),
        (b'server'                      , b''             ),
        (b'set-cookie'                  , b''             ),
        (b'strict-transport-security'   , b''             ),
        (b'transfer-encoding'           , b''             ),
        (b'user-agent'                  , b''             ),
        (b'vary'                        , b''             ),
        (b'via'                         , b''             ),
        (b'www-authenticate'            , b''             ),
    )

    def __init__(self):
        self._maxsize = HeaderTable.DEFAULT_SIZE
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
        if index < 0:
            return None # TODO throw HPACKException here
        if index < len(HeaderTable.STATIC_TABLE):
            return HeaderTable.STATIC_TABLE[index]
        index -= len(HeaderTable.STATIC_TABLE)
        if index < len(self.dynamic_entries):
            return self.dynamic_entries[index]
        return None # TODO throw HPACKException here

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
        if table_entry_size(name, value) > self._maxsize:
            self.dynamic_entries.clear()

        # Add new entry if the table actually has a size
        elif self._maxsize > 0:
            self.dynamic_entries.appendleft((name, value))
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
        offset = len(HeaderTable.STATIC_TABLE)
        partial = None
        for (i, (n, v)) in enumerate(HeaderTable.STATIC_TABLE):
            if n == name:
                if v == value:
                    return (i + 1, n, v)
                elif partial is None:
                    partial = (i + 1, n, None)
        for (i, (n, v)) in enumerate(self.dynamic_entries):
            if n == name:
                if v == value:
                    return (i + offset + 1, n, v)
                elif partial is None:
                    partial = (i + offset + 1, n, None)
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
        elif oldmax > newmax:
            self._shrink()

    def _size(self):
        """
        Calculates the size of the dynamic table.
        See table_entry_size
        See RFC7541 Section 4.1
        """
        return sum(table_entry_size(*entry) for entry in self.dynamic_entries)

    def _shrink(self):
        """
        Shrinks the dynamic table to be at or below maxsize
        """
        cursize = self._size()
        while cursize > self._maxsize:
            (name, value) = self.dynamic_entries.pop()
            cursize -= table_entry_size(name, value)
            log.debug("Evicting %s: %s from the header table", name, value)
