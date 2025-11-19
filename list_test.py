#!/usr/bin/env -S uv run pytest --asyncio-mode auto -k test_list_j
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest-asyncio"]
# ///

# Or Run this file directly with ./list_test.py
# if you're worred that pytest is messing something up
# and to see output

DEBUG = False

import sys
IN_PYTEST = 'pytest' in sys.modules

# For manual running, adjust these parameters:
src_name ='list_literal'
mode='compile'


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
"""
}

@pytest.mark.parametrize("src_name", ["generic", "list_literal"])
@pytest.mark.parametrize("mode", ["compile", "redshift_and_run"])
# @pytest.mark.parametrize("src_name", ["generic"])
# @pytest.mark.parametrize("do_compile_key", ["compile_True"])
async def test_list_j(src_name, mode):
    if IN_PYTEST:
        if src_name == "list_literal" and mode == "compile":
            pytest.xfail("This is the feature we're implementing")
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
    modname = args.filename.stem        # These lines are critical or we can't analyze imports later
    assert modname == 'list_test_src'   #
    srcdir = args.filename.parent       #
    vm.path.append(str(srcdir)) 
    importer = ImportAnalyzer(vm, modname)
    debug("ImportAnalyzer created") 
    # TODO What can we assert here?


    # Parse all imports
    importer.parse_all()
    assert importer.mods
    debug(f"After parse_all() importer.mods = {shorten(str(importer.mods), 120)}")
    # TODO What can we assert here?


    # Import all modules found earlier
    importer.import_all()
    debug(f"After import_all(), {shorten(str(vm.modules_w), 120)}")
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
    #asyncio.run(test_list_j(src_name='generic', mode='redshift_and_run'))
    asyncio.run(test_list_j(src_name=src_name, mode=mode))
