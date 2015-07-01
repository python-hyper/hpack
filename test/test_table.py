from hpack.table import HeaderTable
import pytest

class TestHeaderTable(object):
    def test_getitem_dynamic_table(self):
        tbl = HeaderTable()
        off = len(HeaderTable.STATIC_TABLE)
        val = (b'TestName', b'TestValue')
        tbl.add(val[0], val[1])
        res = tbl[off + 1]
        assert res == val

    def test_getitem_static_table(self):
        tbl = HeaderTable()
        exp = HeaderTable.STATIC_TABLE[0]
        res = tbl[1]
        assert res == exp
        off = len(HeaderTable.STATIC_TABLE)
        exp = HeaderTable.STATIC_TABLE[off - 1]
        res = tbl[off]
        assert res == exp

    def test_getitem_zero_index(self):
        tbl = HeaderTable()
        res = tbl[0]
        assert res == None # TODO HPACKException will be raised instead

    def test_getitem_out_of_range(self):
        tbl = HeaderTable()
        off = len(HeaderTable.STATIC_TABLE)
        tbl.add(b'TestName', b'TestValue')
        res = tbl[off+2]
        assert res == None # TODO HPACKException will be reaised instead

    def test_setitem(self):
        tbl = HeaderTable()
        with pytest.raises(TypeError) as einfo:
            tbl[1] = (b'TestName', b'TestValue')
        assert 'HeaderTable' in str(einfo.value)

    def test_repr(self):
        tbl = HeaderTable()
        tbl.add(b'TestName1', b'TestValue1')
        tbl.add(b'TestName2', b'TestValue2')
        tbl.add(b'TestName2', b'TestValue2')
        exp = ("HeaderTable(4096, False, ["    +
               "('TestName2', 'TestValue2'), " +
               "('TestName2', 'TestValue2'), " +
               "('TestName1', 'TestValue1')"   +
               "])")
        res = str(tbl)
        assert res == exp

    def test_add_to_large(self):
        tbl = HeaderTable()
        # Max size to small to hold the value we specify
        tbl.maxsize = 17 + 31
        tbl.add(b'TestName', b'TestValue')
        # Table length should be 0
        assert len(tbl) == 0

    def test_search_in_static_full(self):
        tbl = HeaderTable()
        itm = HeaderTable.STATIC_TABLE[0]
        exp = (1, itm[0], itm[1])
        res = tbl.search(itm[0], itm[1])
        assert res == exp

    def test_search_in_static_partial(self):
        tbl = HeaderTable()
        itm = HeaderTable.STATIC_TABLE[0]
        exp = (1, itm[0], None)
        res = tbl.search(itm[0], b'NotInTable')
        assert res == exp

    def test_search_in_dynamic_full(self):
        tbl = HeaderTable()
        idx = len(HeaderTable.STATIC_TABLE)+1
        tbl.add(b'TestName', b'TestValue')
        exp = (idx , b'TestName', b'TestValue')
        res = tbl.search(b'TestName', b'TestValue')
        assert res == exp

    def test_search_in_dynamic_partial(self):
        tbl = HeaderTable()
        idx = len(HeaderTable.STATIC_TABLE)+1
        tbl.add(b'TestName', b'TestValue')
        exp = (idx , b'TestName', None)
        res = tbl.search(b'TestName', b'NotInTable')
        assert res == exp

    def test_search_no_match(self):
        tbl = HeaderTable()
        idx = len(HeaderTable.STATIC_TABLE)
        tbl.add(b'TestName', b'TestValue')
        exp = None
        res = tbl.search(b'NotInTable', b'NotInTable')
        assert res == exp

    def test_maxsize_prop_getter(self):
        tbl = HeaderTable()
        assert tbl._maxsize == HeaderTable.DEFAULT_SIZE

    def test_maxsize_prop_setter(self):
        tbl = HeaderTable()
        exp = int(HeaderTable.DEFAULT_SIZE / 2)
        tbl.maxsize = exp
        assert tbl.resized == True
        assert tbl._maxsize == exp
        tbl.resized = False
        tbl.maxsize = exp
        assert tbl.resized == False
        assert tbl._maxsize == exp

    def test_entry_size(self):
        tbl = HeaderTable()
        exp = 32 + len(b'TestValue') + len(b'TestName')
        res = tbl._entry_size(b'TestValue', b'TestName')
        assert res == exp

    def test_size(self):
        tbl = HeaderTable()
        exp = 3*(32 + len(b'TestValue') + len(b'TestName'))
        for i in xrange(3):
            tbl.add(b'TestValue', b'TestName')
        res = tbl._size()
        assert res == exp

    def test_shrink_maxsize_is_zero(self):
        tbl = HeaderTable()
        tbl.add(b'TestName',b'TestValue')
        assert len(tbl) == 1
        tbl.maxsize = 0
        assert len(tbl) == 0
