import pytest

from spy.fqn import FQN
from spy.tests.support import CompilerTest, expect_errors, no_C, only_interp
from spy.vm.b import B
from spy.vm.object import W_Type
from spy.vm.slice import W_Slice


class Test_Slice(CompilerTest):
    @only_interp
    def test_slice_builtin(self):
        mod = self.compile("""
            def foo() -> Slice:
                return slice(1, 2, 3)
            """)
        x = mod.foo()
        assert x == slice(1, 2, 3)

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
