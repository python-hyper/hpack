# cython: language = c++
import logging
from typing import Optional

from libcpp.deque cimport deque

from ._exceptions cimport InvalidTableIndex

from cpython.long cimport PyLong_FromSsize_t

from cpython.object cimport PyObject
from cpython.bytes cimport PyBytes_GET_SIZE, PyBytes_FromString, PyBytes_AS_STRING
from cpython.dict cimport PyDict_SetItemString, PyDict_SetItem, PyDict_GetItem, PyDict_GetItemString
from cpython.ref cimport Py_INCREF, Py_DECREF

log = logging.getLogger(__name__)

cdef extern from "Python.h":
    # Recast hack for Tuples
    object PyTuple_GET_ITEM(PyObject* p, Py_ssize_t pos)


cdef extern from *:
    """
static const char* STATIC_TABLE[61][2] = {
    {":authority"                  ,""             },
    {":method"                     ,"GET"          },
    {":method"                     ,"POST"         },
    {":path"                       ,"/"            },
    {":path"                       ,"/index.html"  },
    {":scheme"                     ,"http"         },
    {":scheme"                     ,"https"        },
    {":status"                     ,"200"          },
    {":status"                     ,"204"          },
    {":status"                     ,"206"          },
    {":status"                     ,"304"          },
    {":status"                     ,"400"          },
    {":status"                     ,"404"          },
    {":status"                     ,"500"          },
    {"accept-charset"              ,""             },
    {"accept-encoding"             ,"gzip, deflate"},
    {"accept-language"             ,""             },
    {"accept-ranges"               ,""             },
    {"accept"                      ,""             },
    {"access-control-allow-origin" ,""             },
    {"age"                         ,""             },
    {"allow"                       ,""             },
    {"authorization"               ,""             },
    {"cache-control"               ,""             },
    {"content-disposition"         ,""             },
    {"content-encoding"            ,""             },
    {"content-language"            ,""             },
    {"content-length"              ,""             },
    {"content-location"            ,""             },
    {"content-range"               ,""             },
    {"content-type"                ,""             },
    {"cookie"                      ,""             },
    {"date"                        ,""             },
    {"etag"                        ,""             },
    {"expect"                      ,""             },
    {"expires"                     ,""             },
    {"from"                        ,""             },
    {"host"                        ,""             },
    {"if-match"                    ,""             },
    {"if-modified-since"           ,""             },
    {"if-none-match"               ,""             },
    {"if-range"                    ,""             },
    {"if-unmodified-since"         ,""             },
    {"last-modified"               ,""             },
    {"link"                        ,""             },
    {"location"                    ,""             },
    {"max-forwards"                ,""             },
    {"proxy-authenticate"          ,""             },
    {"proxy-authorization"         ,""             },
    {"range"                       ,""             },
    {"referer"                     ,""             },
    {"refresh"                     ,""             },
    {"retry-after"                 ,""             },
    {"server"                      ,""             },
    {"set-cookie"                  ,""             },
    {"strict-transport-security"   ,""             },
    {"transfer-encoding"           ,""             },
    {"user-agent"                  ,""             },
    {"vary"                        ,""             },
    {"via"                         ,""             },
    {"www-authenticate"            ,""             },
};
    """
    const char** STATIC_TABLE[61]

cpdef Py_ssize_t table_entry_size(bytes name, bytes value):
    """
    Calculates the size of a single entry

    This size is mostly irrelevant to us and defined
    specifically to accommodate memory management for
    lower level implementations. The 32 extra bytes are
    considered the "maximum" overhead that would be
    required to represent each entry in the table.

    See RFC7541 Section 4.1
    """
    return 32 + PyBytes_GET_SIZE(name) + PyBytes_GET_SIZE(value)


DEF DEFAULT_SIZE = 4096
DEF STATIC_TABLE_LENGTH = 61

cdef dict _build_static_table_mapping():
    # Build static table mapping from header name to tuple with next structure:
    # (<minimal index of header>, <mapping from header value to it index>).

    # static_table_mapping used for hash searching.
    
    cdef dict static_table_mapping  = {}
    cdef dict header_name_search_result
    cdef Py_ssize_t index 
    cdef bytes value
    for index in range(62):
        header_name_search_result = {}
        
        value = PyBytes_FromString(STATIC_TABLE[index][1])
        if PyDict_SetItem(header_name_search_result, index, value) < 0:
            raise

        if PyDict_SetItemString(static_table_mapping, STATIC_TABLE[index][0], tuple(
            index, 
            header_name_search_result
        )) < 0:
            raise

    return static_table_mapping

# Bypass Mechanism
ctypedef PyObject* PyPair[2]

cdef class HeaderTable:
    """
    Implements the combined static and dynamic header table

    The name and value arguments for all the functions
    should ONLY be byte strings (b'') however this is not
    strictly enforced in the interface.

    See RFC7541 Section 2.3
    """
    cdef Py_ssize_t _maxsize
    cdef Py_ssize_t _current_size
    cdef dict STATIC_TABLE_MAPPING
    cdef readonly bint resized
    cdef deque[PyPair] dynamic_entries

    def __init__(self) -> None:
        self._maxsize = DEFAULT_SIZE
        self._current_size = 0
        self.resized = False
        self.STATIC_TABLE_MAPPING = _build_static_table_mapping()

    cpdef tuple get_by_index(self, size_t index):
        """
        Returns the entry specified by index

        Note that the table is 1-based ie an index of 0 is
        invalid.  This is due to the fact that a zero value
        index signals that a completely unindexed header
        follows.

        The entry will either be from the static table or
        the dynamic table depending on the value of index.
        """
        cdef size_t original_index = index
        cdef PyPair pair
        cdef char* char_pair[2]
        index -= 1
        if 0 <= index:
            if index < STATIC_TABLE_LENGTH:
                char_pair = STATIC_TABLE[index]
                return char_pair[0], char_pair[1]

            index -= STATIC_TABLE_LENGTH
            if index < self.dynamic_entries.size():
                pair = self.dynamic_entries[index]
            return <object>pair[0], <object>pair[1]

        raise InvalidTableIndex("Invalid table index %d" % original_index)
    # TODO: Custom Repr for self.dynamic_entries

    def __repr__(self) -> str:
        return "HeaderTable(%d, %s)" % (
            self._maxsize,
            self.resized,
        )

    cpdef object add(self, bytes name, value: bytes):
        """
        Adds a new entry to the table

        We reduce the table size if the entry will make the
        table size greater than maxsize.
        """
        # We just clear the table if the entry is too big
        cdef PyPair nv
        cdef Py_ssize_t size = table_entry_size(name, value)
        if size > self._maxsize:
            self.dynamic_entries.clear()
            self._current_size = 0
        else:
            # Add new entry
            nv[0] = <PyObject*>name
            nv[1] = <PyObject*>value
            self.dynamic_entries.push_front(nv)
 
            self._current_size += size
            self._shrink()

    cpdef object search(self, name: bytes, value: bytes):
        """
        Searches the table for the entry specified by name
        and value

        Returns one of the following:
            - ``None``, no match at all
            - ``(index, name, None)`` for partial matches on name only.
            - ``(index, name, value)`` for perfect matches.
        """
        cdef object partial = None
        cdef PyObject* header_name_search_result = PyDict_GetItemString(self.STATIC_TABLE_MAPPING, PyBytes_AS_STRING(name))
        cdef PyObject* index
        cdef size_t i
        cdef object n, v
        cdef PyObject* tup[2]

        if header_name_search_result != NULL:
            index = PyDict_GetItemString(PyTuple_GET_ITEM(header_name_search_result, 1), PyBytes_AS_STRING(value))
            if index != NULL:
                return <object>index, name, value
            else:
                partial = (PyTuple_GET_ITEM(header_name_search_result, 0), name, None)

        offset = STATIC_TABLE_LENGTH + 1
        for i in self.dynamic_entries.size():
            tup = self.dynamic_entries.at(i)
            # depack tuple
            n = <object>tup[0]
            v = <object>tup[1]

            if n == name:
                if v == value:
                    return i + offset, n, v
                elif partial is None:
                    partial = (i + offset, n, None)

        return partial

    @property
    def maxsize(self) -> int:
        return self._maxsize

    @maxsize.setter
    def maxsize(self, Py_ssize_t newmax) -> None:
        cdef Py_ssize_t oldmax
     
        log.debug("Resizing header table to %d from %d", newmax, self._maxsize)
        oldmax = self._maxsize
        self._maxsize = newmax
        self.resized = (newmax != oldmax)
        if newmax <= 0:
            self.dynamic_entries.clear()
            self._current_size = 0
        elif oldmax > newmax:
            self._shrink()

    cpdef object _shrink(self):
        """
        Shrinks the dynamic table to be at or below maxsize
        """
        cdef Py_ssize_t cursize = self._current_size
        cdef PyPair kv
        cdef object name, value
        while cursize > self._maxsize:
            kv = self.dynamic_entries.back()
            name = <object>kv[0]
            value = <object>kv[1]
            cursize -= table_entry_size(name, value)
            log.debug("Evicting %s: %s from the header table", name, value)
            self.dynamic_entries.pop_back()

        self._current_size = cursize

