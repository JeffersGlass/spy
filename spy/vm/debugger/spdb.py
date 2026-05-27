"""
The SPy debugger ("spy pdb")
"""

import cmd
import pdb
import sys
from contextlib import contextmanager
from typing import IO, TYPE_CHECKING, Annotated, Any, Literal, Optional

from spy import ast
from spy.doppler import DopplerFrame
from spy.errfmt import ErrorFormatter
from spy.errors import SPyError
from spy.location import Loc
from spy.magic_py_parse import PythonParseException
from spy.parser import Parser
from spy.textbuilder import ColorFormatter
from spy.util import record_src_in_linecache
from spy.vm.astframe import ASTFrame
from spy.vm.b import BUILTINS
from spy.vm.classframe import ClassFrame
from spy.vm.debugger.longlist import print_longlist
from spy.vm.exc import FrameInfo, W_Traceback
from spy.vm.modframe import ModFrame
from spy.vm.modules.operator import OP
from spy.vm.opspec import W_MetaArg
from spy.vm.w import W_Object

if TYPE_CHECKING:
    from spy.vm.vm import SPyVM

FILE = Optional[IO[str]]


@BUILTINS.builtin_func
def w_breakpoint(vm: "SPyVM") -> None:
    spdb = make_spdb(vm)
    spdb.interaction()


def make_spdb(vm: "SPyVM", **kwargs: Any) -> "SPdb":
    # generate a fake traceback
    pyframe = sys._getframe().f_back.f_back  # type: ignore
    assert pyframe is not None
    w_tb = W_Traceback.from_py_frame(pyframe)
    spdb = SPdb(vm, w_tb, **kwargs)
    return spdb


def print_wam(
    vm: "SPyVM", wam_arg: W_MetaArg, *, file: FILE = None, use_colors: bool = True
) -> None:
    if file is None:
        file = sys.stdout
    w_T = vm.dynamic_type(wam_arg.w_val)
    wam_s = vm.repr_wam(wam_arg, loc=Loc.here())
    s = vm.unwrap_str(wam_s.w_val)
    #
    color = ColorFormatter(use_colors=use_colors)
    print(color.set("green", "static type: "), wam_arg.w_static_T, file=file)
    print(color.set("green", "dynamic type:"), w_T, file=file)
    print(s, file=file)


class SPdbInput:
    def __init__(self, spdb_instance, stdin, stdout, prompt):
        import os

        import _pyrepl.readline

        self.spdb_instance = spdb_instance
        self.prompt = prompt
        if not (os.isatty(stdin.fileno())):
            raise ValueError("stdin is not a TTY")
        self.readline_wrapper = _pyrepl.readline._ReadlineWrapper(
            f_in=stdin.fileno(),
            f_out=stdout.fileno(),
            config=_pyrepl.readline.ReadlineConfig(
                completer_delims=frozenset(" \t\n`@#%^&*()=+[{]}\\|;:'\",<>?")
            ),
        )

    def readline(self):
        def more_lines(text: str) -> bool:
            if text.strip() == "\x1a":
                # Ctrl + Z raises EOFError to quit pdb
                # This is similarly handled in simple_interact.py
                raise EOFError
            cmd, _, line = self.spdb_instance.parseline(text)
            if not line or not cmd:
                return False
            func = getattr(self.pdb_instance, "do_" + cmd, None)
            if func is not None:
                return False
            return self.more_lines(text)

        try:
            multiline = (
                self.readline_wrapper.multiline_input(
                    more_lines, self.prompt, "... " + " " * (len(self.prompt) - 4)
                )
                + "\n"
            )
            return multiline
        except EOFError:
            return "EOF"

    @staticmethod
    def more_lines(text: str) -> bool:
        src = text.rstrip(" \t")
        n = len(src)
        if n > 0 and text[n - 1] == "\n":
            text = src
        try:
            filename = record_src_in_linecache(text, name="spdb-eval")
            parser = Parser(text, filename)
            stmt = parser.parse_single_stmt(raise_as_python=True)
        except PythonParseException:
            lines = text.splitlines(keepends=True)
            if len(lines) == 1:
                return False
            last = lines[-1]
            return (
                last.startswith((" ", "\t")) or last.strip() != ""
            ) and not last.endswith("\n")
        return len(stmt.body) > 0


class SPdb(cmd.Cmd):
    prompt = "(spdb🥸) "

    def __init__(
        self,
        vm: "SPyVM",
        w_tb: W_Traceback,
        *,
        stdin: FILE = None,
        stdout: FILE = None,
        use_colors: bool = True,
    ) -> None:
        super().__init__(stdin=stdin, stdout=stdout)
        if stdin is not None and stdin is not sys.stdin:
            self.use_rawinput = False

        self._raw_stdin = self.stdin
        self._raw_stdout = self.stdout
        self.repl_input = None
        if stdin is None:
            try:
                self.repl_input = SPdbInput(self, self.stdin, self.stdout, self.prompt)
                self.stdin = self.repl_input
            except Exception:
                pass

        self.use_colors = use_colors
        self.vm = vm
        self.w_tb = w_tb
        self.curindex = -1  # currently selected frame

    def interaction(self) -> None:
        print("--- entering applevel debugger ---", file=self.stdout)
        last = len(self.w_tb.entries) - 1
        self.select_frame(last)
        self.cmdloop()

    def post_mortem(self) -> None:
        print("--- entering applevel debugger (post-mortem) ---", file=self.stdout)
        last = len(self.w_tb.entries) - 1
        self.select_frame(last)
        try:
            self.cmdloop()
        except SPyError as e:
            if e.etype == "W_SPdbQuit":
                return
            raise

    def select_frame(self, i: int) -> None:
        assert 0 <= i < len(self.w_tb.entries)
        if self.curindex != i:
            self.curindex = i
            self.print_frame_info(i)

    def get_curframe(self) -> FrameInfo:
        return self.w_tb.entries[self.curindex]

    def print_frame_info(self, i: int) -> None:
        f = self.w_tb.entries[i]
        errfmt = ErrorFormatter(use_colors=self.use_colors)
        errfmt.emit_frameinfo(f, index=i)
        print(errfmt.build(), end="", file=self.stdout)

    def error(self, msg: str) -> None:
        print("***", msg, file=self.stdout)

    def default(self, arg: str) -> None:
        self.vm.exec_source(arg, frame=self.get_curframe().spyframe)

        # If the source is an expression, we need to print its value
        null_result = object()
        result = null_result
        filename = record_src_in_linecache(arg, name="spdb-eval")
        parser = Parser(arg, filename)
        try:
            parser.parse_single_expr()
        except PythonParseException:
            pass
        else:
            self.do_print(arg)

    def do_quit(self, arg: str) -> None:
        raise SPyError("W_SPdbQuit", "")

    do_q = do_quit

    def do_continue(self, arg: str) -> bool:
        return True

    do_c = do_continue
    do_cont = do_continue

    def do_where(self, arg: str) -> None:
        """w(here)

        Print a stack trace, with the most recent frame at the bottom.
        """
        errfmt = ErrorFormatter(use_colors=self.use_colors)
        for i, f in enumerate(self.w_tb.entries):
            errfmt.emit_frameinfo(f, index=i, is_current=(i == self.curindex))
        print(errfmt.build(), end="", file=self.stdout)

    do_w = do_where
    do_bt = do_where

    def do_up(self, arg: str) -> None:
        """u(p) [count]

        Move the current frame count (default one) levels up in the
        stack trace (to an older frame).
        """
        if self.curindex == 0:
            self.error("Oldest frame")
            return
        try:
            count = int(arg or 1)
        except ValueError:
            self.error("Invalid frame count (%s)" % arg)
            return
        if count < 0:
            newframe = 0
        else:
            newframe = max(0, self.curindex - count)
        self.select_frame(newframe)

    do_u = do_up

    def do_down(self, arg: str) -> None:
        """d(own) [count]

        Move the current frame count (default one) levels down in the
        stack trace (to a newer frame).
        """
        if self.curindex + 1 == len(self.w_tb.entries):
            self.error("Newest frame")
            return
        try:
            count = int(arg or 1)
        except ValueError:
            self.error("Invalid frame count (%s)" % arg)
            return
        if count < 0:
            newframe = len(self.w_tb.entries) - 1
        else:
            newframe = min(len(self.w_tb.entries) - 1, self.curindex + count)
        self.select_frame(newframe)

    do_d = do_down

    def do_longlist(self, arg: str) -> None:
        """l | ll | list | longlist

        List the whole source code for the current function or frame.
        """
        f = self.get_curframe()
        if f.kind in ("astframe", "dopplerframe"):
            spyframe = f.spyframe
            assert isinstance(spyframe, ASTFrame)
            # Get the function location and current location
            func_loc = spyframe.loc
            cur_loc = f.loc
            print_longlist(
                func_loc, cur_loc, use_colors=self.use_colors, file=self.stdout
            )
        else:
            print(f"longlist: unsupported kind: {f.kind}")

    do_list = do_longlist
    do_l = do_longlist
    do_ll = do_longlist

    def do_print(self, arg: str) -> None:
        try:
            # eval "arg" in the current frame
            filename = record_src_in_linecache(arg, name="spdb-eval")
            parser = Parser(arg, filename)
            stmt = parser.parse_single_stmt()
            if not isinstance(stmt, ast.StmtExpr):
                clsname = stmt.__class__.__name__
                raise SPyError.simple(
                    "W_WIP",
                    f"not supported by SPdb: {clsname}",
                    "this is not supported",
                    stmt.loc,
                )

            f = self.get_curframe()
            with f.spyframe.interactive():
                f.spyframe.is_interactive = True  # ???
                wam = f.spyframe.eval_expr(stmt.value)
                print_wam(self.vm, wam, file=self.stdout, use_colors=self.use_colors)

        except SPyError as e:
            etype = e.etype[2:]
            message = e.w_exc.message
            self.error(f"{etype}: {message}")

    do_p = do_print

    @contextmanager
    def _replace_attribute(self, attrs):
        original_attrs = {}
        for attr, value in attrs.items():
            original_attrs[attr] = getattr(self, attr)
            setattr(self, attr, value)
        try:
            yield
        finally:
            for attr, value in original_attrs.items():
                setattr(self, attr, value)

    @contextmanager
    def _maybe_use_pyrepl_as_stdin(self):
        if self.pyrepl_input is None:
            yield
            return

        with self._replace_attribute(
            {
                "stdin": self.pyrepl_input,
            }
        ):
            yield
