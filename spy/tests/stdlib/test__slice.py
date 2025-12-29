import pytest

from spy.errors import SPyError
from spy.tests.support import CompilerTest, only_interp


@only_interp
class TestSlice(CompilerTest):
    def test_basic_operations(self):
        src = """
        from _slice import Slice

        def test_create() -> Slice:
            return Slice(0,1,2)
        """
        mod = self.compile(src)
        assert mod.test_create() is not None
