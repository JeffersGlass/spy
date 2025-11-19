# uv run pytest --asyncio-mode auto -k test_list_j

from textwrap import dedent
from pathlib import Path

from spy.analyze.importing import ImportAnalyzer
from spy.cli import Arguments
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

async def test_list_j():
    write_src(GENERIC_SRC)
    args = Arguments(
        filename = SRC_FILE
    )

    modname = args.filename.stem
    assert modname == 'list_test_src'

    vm = await SPyVM.async_new()
    # TODO What can we assert here?

    importer = ImportAnalyzer(vm, modname)
    # TODO What can we assert here?

    importer.parse_all()
    # TODO What can we assert here?

    # Is this load bearing?
    orig_mod = importer.getmod(modname)

    importer.import_all()
    # TODO What can we assert here?

    print(vm.modules_w)
    w_mod = vm.modules_w[modname]
    # TODO What can we assert here?

    # Execute without redshifting
    args.redshift = False
    execute_spy_main(args, vm, w_mod)
    # TODO What can we assert here?

    # Execute WITH redshifting
    args.redshift = True
    execute_spy_main(args, vm, w_mod)
    # TODO What can we assert here?
    