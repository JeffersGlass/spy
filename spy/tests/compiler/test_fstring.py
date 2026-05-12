from itertools import count

from spy.errors import SPyError
from spy.tests.support import CompilerTest, skip_backends


class TestFString(CompilerTest):
    def test_fstring(self):
        # We want to compare a bunch of in-compiler f-strings
        # to their value, but we'd like to only compile the module a
        # single time
        c = count()
        mod = self.compile(
            """
        def s(x: str) -> str:
            return 'abc' f'## {x}ghi'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "abc## defghi"

        return

        mod = self.compile(
            """
        def s(x: str) -> str:
            return 'abc' f'{x}' 'ghi'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "abcdefghi"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return 'abc' f'{x}' 'gh' f'i{x:4}'
        """,
            modname=f"m{next(c)}",
        )
        # assert mod.s('def') == 'abcdefghidef '

        mod = self.compile(
            """
        def s(x: str) -> str:
            return '{x}' f'{x}'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "{x}def"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return '{x' f'{x}'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "{xdef"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return '{x}' f'{x}'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "{x}def"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return '{{x}}' f'{x}'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "{{x}}def"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return '{{x' f'{x}'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "{{xdef"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return 'x}}' f'{x}'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "x}}def"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return f'{x}' 'x}}'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "defx}}"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return f'{x}' ''
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "def"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return '' f'{x}' ''
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "def"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return '' f'{x}'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "def"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return f'{x}' '2'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "def2"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return '1' f'{x}' '2'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "1def2"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return '1' f'{x}'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "1def"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return f'{x}' f'-{x}'
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == "def-def"

        mod = self.compile(
            """
        def s(x: str) -> str:
            return '' f''
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == ""

        mod = self.compile(
            """
        def s(x: str) -> str:
            return '' f'' ''
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == ""

        mod = self.compile(
            """
        def s(x: str) -> str:
            return '' f'' '' f''
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == ""

        mod = self.compile(
            """
        def s(x: str) -> str:
            return f''
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == ""

        mod = self.compile(
            """
        def s(x: str) -> str:
            return f'' ''
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == ""

        mod = self.compile(
            """
        def s(x: str) -> str:
            return f'' '' f''
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == ""

        mod = self.compile(
            """
        def s(x: str) -> str:
            return f'' '' f'' ''
        """,
            modname=f"m{next(c)}",
        )
        assert mod.s("def") == ""
