from collections import deque

class HeaderTable(deque):
    """
    Implements the combined static and dynamic header table

    The name and value arguments for all the functions
    should ONLY be byte arrays (b'') however this is not
    strictly enforced in the interface.

    See RFC7541 Section 2.3

    Class Constants
        DEFAULT_SIZE : Default maximum size of the dynamic
                       table. See RFC7540 Section 6.5.2
        STATIC_TABLE : Constant list of static headers.
                       See RFC7541 Section 2.3.1 and
                       Appendix A
    """

    DEFAULT_SIZE = 4096
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
    (b'www-authenticate'            , b''             ))

    def __init__(self):
        self._maxsize = HeaderTable.DEFAULT_SIZE
        self.resized = False

    def __getitem__(self, index):
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
        if index < len(self):
            return deque.__getitem__(self, index)
        return None # TODO throw HPACKException here

    def __setitem__(self, index, value):
        """
        We don't support direct index setting
        """
        raise TypeError("'HeaderTable' object does not support item assignment, use add")

    def __repr__(self):
        rv = "HeaderTable("
        rv += str(self._maxsize)
        rv += ","+str(self.resized)
        rv += ",["
        for entry in self:
            rv += str(entry)
        return rv+"])"

    def add(self, name, value):
        """
        Adds a new entry to the table

        We reduce the table size if the entry will make the
        table size greater than maxsize.
        """
        # We just clear the table if the entry is to big
        if self._entry_size(name, value) > self._maxsize:
          self.clear()
        # Add new entry if the table actually has a size
        elif self._maxsize > 0:
          self.appendleft((name,value))
          self._shrink()

    def search(self, name, value):
        """
        Searchs the table for the entry spefied by name and
        value

        Returns one of the following:
            None                 no match at all
            (index, name, None)  partial match (on name)
            (index, name, value) perfect match
        """
        offset = len(HeaderTable.STATIC_TABLE)
        partial = None
        for (i, (n, v)) in enumerate(HeaderTable.STATIC_TABLE):
            if n == name:
                if v == value:
                    return (i + 1, n, v)
                elif partial is None:
                    partial = (i + 1, n, None)
        for (i, (n, v)) in enumerate(self):
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
        oldmax = self._maxsize
        self._maxsize = newmax
        self.resized = (newmax != oldmax)
        if newmax <= 0:
          self.clear()
        elif oldmax > newmax:
          self._shrink()

    def _entry_size(self, name, value):
        """
        Calculates the size of a single entry

        This size is mostly irrelevant to us and defined
        specifically to accomidate memory management for
        lower level implementions. The 32 extra bytes are
        considered the "maximum" overhead that would be
        required to represent each entry in the table.

        See RFC7541 Section 4.1
        """
        return 32 + len(name) + len(value)

    def _size(self):
        """
        Calculates the size of the dynamic table.
        See _entry_size
        See RFC7541 Section 4.1
        """
        size = 0
        for (name, value) in self:
            size += self._entry_size(name, value)
        return size

    def _shrink(self):
        """
        Shrinks the dynamic table to be at or below maxsize
        """
        cursize = self._size()
        while cursize > self._maxsize:
            (name, value) = self.pop()
            cursize -= self._entry_size(name, value)

