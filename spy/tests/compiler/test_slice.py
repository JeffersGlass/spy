import pytest

from spy.fqn import FQN
from spy.tests.support import CompilerTest, expect_errors, no_C, only_interp
from spy.vm.b import B


class Test_Slice(CompilerTest):
    @only_interp
    def test_slice_builtin(self):
        mod = self.compile("""
            def foo() -> Slice:
                return slice(1, 2, 3)
            """)
        x = mod.foo()
        assert x == slice(1, 2, 3)
