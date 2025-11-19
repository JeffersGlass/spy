#!/usr/bin/env -S uv run pytest --asyncio-mode auto -k test_list_j -v -s

#Run this file directly with ./list_test.py

from textwrap import dedent, shorten
from pathlib import Path

import pytest
import py.path

from spy.analyze.importing import ImportAnalyzer
from spy.backend.c.cbackend import CBackend
from spy.build.config import BuildConfig, BuildTarget, OutputKind
from spy.cli import Arguments, execute_spy_main
from spy.vm.vm import SPyVM


SRC_FILE_PATH = Path('list_test_src.spy')

sources = {
    "generic": """\
#Generic
def main() -> None:
    a = 1 + 2
    print(a)
""", 
    "list_literal": """\
#list
def main() -> None:
    m = [1,2,3]
    m.append(4)
    print(m)
"""
}

def write_src(src):
    with open(SRC_FILE_PATH, "w") as f:
        f.write(dedent(src))

redshifts = {
    "redshift_True" : True,
    "redshift_False" : False
}

do_compile = {
    "compile_True" : True,
    "compile_False" : False
}

@pytest.mark.parametrize("src_name", ["generic", "list_literal"])
@pytest.mark.parametrize("redshift_key", ["redshift_True", "redshift_False"])
@pytest.mark.parametrize("do_compile_key", ["compile_False", "compile_True"])
async def test_list_j(redshift_key, src_name, do_compile_key):
    print(f"\n---Running pipeline with {redshift_key=}---")

    # Write the source selection to a file
    src = sources[src_name]
    write_src(src) # CHANGE ME TO CHANGE SOURCE
    args = Arguments(
        filename = SRC_FILE_PATH,
        redshift = redshifts[redshift_key]
    )
    print("Wrote src to file") 


    # Start up a VM instance
    vm = await SPyVM.async_new()
    print("vm initializaed") 
    # TODO What can we assert here?


    # Create an ImportAnalyzer tied to the vm and associated with the module given
    modname = args.filename.stem        # These lines are critical or we can't analyze imports later
    assert modname == 'list_test_src'   #
    srcdir = args.filename.parent       #
    vm.path.append(str(srcdir)) 
    importer = ImportAnalyzer(vm, modname)
    print("ImportAnalyzer created") 
    # TODO What can we assert here?


    # Parse all imports
    importer.parse_all()
    assert importer.mods
    print(f"After parse_all() importer.mods = {shorten(str(importer.mods), 120)}")
    # TODO What can we assert here?


    # Import all modules found earlier
    importer.import_all()
    print(f"After import_all(), {shorten(str(vm.modules_w), 120)}")
    orig_mod = importer.getmod(modname) # Peek at the module we wanted to run
    w_mod = vm.modules_w[modname]
    print(f"{w_mod=}")
    # TODO What can we assert here?
    

    # Redshift if desired
    if args.redshift:
        vm.redshift(error_mode="eager")

    # Run the Module
    print("--- Calling spy_main ---")
    execute_spy_main(args, vm, w_mod)
    print("--- spy_main done ---")


    if args.redshift:
        ... # TODO What can we assert here?
    else:
        ... # TODO What can we assert here?

    if not do_compile[do_compile_key]:
        return

    # Write the C files
    ### This is straight from cli.inner_main
    config = BuildConfig(
        target=args.target,
        kind=args.output_kind,
        build_type="release" if args.release_mode else "debug",
    )

    cwd = py.path.local(".")
    build_dir = srcdir / "build"
    build_dir.mkdir(exist_ok=True, parents=True)
    build_dir =  py.path.local(str(build_dir))
    dump_c = args.cwrite and args.cdump
    srcdir = args.filename.parent
    backend = CBackend(vm, modname, config, build_dir, dump_c=False)

    backend.cwrite()
    backend.write_build_script()

    outfile = backend.build()
    ... # TODO What can we assert here?
    

    print("\n\n")
    