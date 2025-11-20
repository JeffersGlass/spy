#!/usr/bin/env -S uv run pytest --asyncio-mode auto -k test_list_j -v
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest-asyncio"]
# ///

# Or Run this file directly with ./list_test.py
# if you're worred that pytest is messing something up
# and to see output

DEBUG = True

import sys
IN_PYTEST = 'pytest' in sys.modules


import asyncio
from pathlib import Path
from textwrap import dedent, shorten

import pytest
import py.path

from spy.analyze.importing import ImportAnalyzer
from spy.backend.c.cbackend import CBackend
from spy.build.config import BuildConfig, BuildTarget, OutputKind
from spy.cli import Arguments, execute_spy_main, get_build_dir
from spy.vm.vm import SPyVM


def debug(*args, **kwargs):
    if not DEBUG: return
    print(*args, **kwargs)

SRC_FILE_PATH = Path('list_test_src.spy')

sources = {
    "generic": """\
#Generic
def main() -> None:
    foo()

def foo() -> None:
    a: i32 = 1 + 2
    print(a)
""", 

    "list_literal": """\
#list
def main() -> None:
    m = [1,2,3]
    print(m)
""",

    "list_add": """\
#list
def main() -> None:
    p = [1,2,3] + [4,5,6]
    print(p)
""",

    "list_mul": """\
#list
def main() -> None:
    q = [1,2,3] * 2
    print(q)
""",

    "tuple_literal": """\
#tuple
def main() -> None:
    r = (1, 2, 3)
    print(r)
    """,

    "import_list": """\
#import_list
from _list import List
def main() -> None:
    lst = List[int]()
    """

}

@pytest.fixture
def xfail_selected_params(request):
    # This is the feature we're implementing
    src_name = request.getfixturevalue('src_name')
    mode = request.getfixturevalue('mode')

    allowed_failures = {
        ("list_literal", "compile"): "Cannot compile builtin-lists",
        ("list_add", "compile"): "Cannot compile builtin-lists",
        ("list_mul", "compile"): "Cannot compile builtin-lists",
        ("list_mul", "redshift_and_run"): "No support for list.__mul__ in vm.list",
    }
    if (src_name, mode) in allowed_failures:
        request.node.add_marker(pytest.mark.xfail(reason=allowed_failures[(src_name, mode)]))

@pytest.mark.parametrize("src_name", ["generic", "list_literal", "list_add", "list_mul", "tuple_literal"])
@pytest.mark.parametrize("mode", ["compile", "redshift_and_run"])
async def test_list_j(src_name, mode, xfail_selected_params):
    # Write the source selection to a file
    src = sources[src_name]

    with open(SRC_FILE_PATH, "w") as f:
        f.write(dedent(src))
    debug("Wrote src to file") 
    args = Arguments(
        filename = SRC_FILE_PATH,
        redshift = (mode == 'redshift_and_run'),
        compile = (mode == 'compile'),
    )
    args.validate_actions()


    # Start up a VM instance
    vm = await SPyVM.async_new()
    debug("vm initializaed") 
    # TODO What can we assert here?


    # Create an ImportAnalyzer tied to the vm and associated with the module given
    modname = args.filename.stem        # | These lines are critical or we can't analyze imports later
    assert modname == 'list_test_src'   # |
    srcdir = args.filename.parent       # |
    vm.path.append(str(srcdir))         # |
    importer = ImportAnalyzer(vm, modname)
    debug("ImportAnalyzer created") 
    # TODO What can we assert here?


    # Parse the python file, and find all imports
    # I think (some?) the magic can happen here - as part of the parsing step, we
    # we parse the imports. We can detect any List nodes at this stage
    importer.parse_all()
    assert importer.mods
    #debug(f"After parse_all() importer.mods={shorten(str(importer.mods), 120)}")
    debug(f"After parse_all() importer.mods={importer.mods}")
    # TODO What can we assert here?

    if src_name  in ("list_literal", "import_list"):
        assert '_list' in importer.mods


    # Import all modules found earlier. Also does analyze_scopes
    importer.import_all()
    #debug(f"After import_all(), vm.modules_w={shorten(str(vm.modules_w), 120)}")
    # We could use the above flag here to know whether we need to import the _list module?
    debug(f"After import_all(), vm.modules_w=")
    for m in vm.modules_w:
        debug(f"\t{m}")
    if 'list_test_src' in vm.modules_w:
        debug(f"{vm.modules_w['list_test_src']=}")
    orig_mod = importer.getmod(modname) # Peek at the module we wanted to run
    w_mod = vm.modules_w[modname]
    debug(f"{w_mod=}")
    # TODO What can we assert here?
    

    vm.redshift(error_mode="eager")
    ... # TODO What can we assert here?

    
    # Run the Module
    if not args.compile:
        debug("--- Calling spy_main without compiling ---")
        execute_spy_main(args, vm, w_mod)
        debug("--- spy_main done ---")
        return


    # Write the C files
    ### This is straight from cli.inner_main
    config = BuildConfig(
        target=args.target,
        kind=args.output_kind,
        build_type="release" if args.release_mode else "debug",
    )
    
    cwd = py.path.local(".")
    srcdir = args.filename.parent
    build_dir = get_build_dir(args)
    backend = CBackend(vm, modname, config, build_dir, dump_c=False)

    backend.cwrite()
    backend.write_build_script()

    outfile = backend.build()
    ... # TODO What can we assert here?
    

    debug("\n\n")
    
if __name__ == "__main__":
    # For manual running, adjust these parameters:
    src_name = 'list_literal'
    mode='redshift_and_run'

    asyncio.run(test_list_j(src_name=src_name, mode=mode, xfail_selected_params=None))
