#!/usr/bin/env -S uv run pytest --asyncio-mode auto -k test_list_j -v -s

#Run this file directly with ./list_test.py

from textwrap import dedent, shorten
from pathlib import Path

import pytest

from spy.analyze.importing import ImportAnalyzer
from spy.cli import Arguments, execute_spy_main
from spy.vm.vm import SPyVM


SRC_FILE = Path('list_test_src.spy')

GENERIC_SRC = """\
def main() -> None:
    a = 1 + 2
    print(a)
"""

LIST_SRC = """\
def main() -> None:
    m = [1,2,3]
    m.append(4)
    print(m)
"""

def write_src(src):
    with open(SRC_FILE, "w") as f:
        f.write(dedent(src))

@pytest.mark.parametrize("redshift", [True, False])
async def test_list_j(redshift):
    print(f"\n---Running pipeline with {redshift=}---")

    # Write the source selection to a file
    write_src(LIST_SRC) # CHANGE ME TO CHANGE SOURCE
    args = Arguments(
        filename = SRC_FILE,
        redshift = redshift
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
    
    print("\n\n")
    