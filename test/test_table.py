from hpack.table import HeaderTable, table_entry_size
import pytest
import sys
_ver = sys.version_info
is_py2 = _ver[0] == 2
is_py3 = _ver[0] == 3

class TestPackageFunctions(object):
    def test_table_entry_size(self):
        res = table_entry_size(b'TestValue', b'TestName')
        assert res == 49

class TestHeaderTable(object):
    def test_getitem_dynamic_table(self):
        tbl = HeaderTable()
        off = len(HeaderTable.STATIC_TABLE)
        val = (b'TestName', b'TestValue')
        tbl.add(*val)
        res = tbl.get_by_index(off + 1)
        assert res == val

    def test_getitem_static_table(self):
        tbl = HeaderTable()
        exp = HeaderTable.STATIC_TABLE[0]
        res = tbl.get_by_index(1)
        assert res == exp
        off = len(HeaderTable.STATIC_TABLE)
        exp = HeaderTable.STATIC_TABLE[off - 1]
        res = tbl.get_by_index(off)
        assert res == exp

    def test_getitem_zero_index(self):
        tbl = HeaderTable()
        res = tbl.get_by_index(0)
        assert res is None # TODO HPACKException will be raised instead

    def test_getitem_out_of_range(self):
        tbl = HeaderTable()
        off = len(HeaderTable.STATIC_TABLE)
        tbl.add(b'TestName', b'TestValue')
        res = tbl.get_by_index(off+2)
        assert res is None # TODO HPACKException will be raised instead

    def test_repr(self):
        tbl = HeaderTable()
        tbl.add(b'TestName1', b'TestValue1')
        tbl.add(b'TestName2', b'TestValue2')
        tbl.add(b'TestName2', b'TestValue2')
        # Meh, I hate that I have to do this to test
        # repr
        if(is_py3):
            exp = ("HeaderTable(4096, False, ["      +
                   "(b'TestName2', b'TestValue2'), " +
                   "(b'TestName2', b'TestValue2'), " +
                   "(b'TestName1', b'TestValue1')"   +
                   "])")
        else:
            exp = ("HeaderTable(4096, False, ["    +
                   "('TestName2', 'TestValue2'), " +
                   "('TestName2', 'TestValue2'), " +
                   "('TestName1', 'TestValue1')"   +
                   "])")
        res = repr(tbl)
        assert res == exp

    def test_add_to_large(self):
        tbl = HeaderTable()
        # Max size to small to hold the value we specify
        tbl.maxsize = 1
        tbl.add(b'TestName', b'TestValue')
        # Table length should be 0
        assert len(tbl.dynamic_entries) == 0

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
        res = tbl.search(b'NotInTable', b'NotInTable')
        assert res is None

    def test_maxsize_prop_getter(self):
        tbl = HeaderTable()
        assert tbl.maxsize == HeaderTable.DEFAULT_SIZE

    def test_maxsize_prop_setter(self):
        tbl = HeaderTable()
        exp = int(HeaderTable.DEFAULT_SIZE / 2)
        tbl.maxsize = exp
        assert tbl.resized == True
        assert tbl.maxsize == exp
        tbl.resized = False
        tbl.maxsize = exp
        assert tbl.resized == False
        assert tbl.maxsize == exp

    def test_size(self):
        tbl = HeaderTable()
        for i in range(3):
            tbl.add(b'TestValue', b'TestName')
        res = tbl._size()
        assert res == 147

    def test_shrink_maxsize_is_zero(self):
        tbl = HeaderTable()
        tbl.add(b'TestName',b'TestValue')
        assert len(tbl.dynamic_entries) == 1
        tbl.maxsize = 0
        assert len(tbl.dynamic_entries) == 0
