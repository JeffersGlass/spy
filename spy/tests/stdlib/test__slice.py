import pytest

from spy.errors import SPyError
from spy.tests.support import CompilerTest, only_interp


class TestSlice(CompilerTest):
    @only_interp
    def test_basic_operations(self):
        src = """
        from _slice import Slice

        def test_create() -> Slice:
            return Slice(0,1,2)
        """
        mod = self.compile(src)
        assert mod.test_create() is not None

    @only_interp
    def test_list_slice_is_list(self):
        mod = self.compile("""
            def foo() -> list[i32]:
                l = [1,2,3]
                return l[0:2:1]
            """)
        x = mod.foo()
        assert type(x) == list

    @pytest.mark.xfail(reason="List slices currently return the whole list")
    @only_interp
    def test_list_slice(self):
        mod = self.compile("""
            def foo() -> list[i32]:
                l = [1,2,3]
                return l[0:2:1]
            """)
        x = mod.foo()
        assert x == [1, 2]
