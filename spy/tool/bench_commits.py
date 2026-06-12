# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "tabulate",
# ]
# ///
import argparse
import itertools
import re
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from statistics import mean
from tempfile import TemporaryDirectory
from typing import Any, Literal

import tabulate

data_interpreter = {
    "name": "spy execute --timeit",
    "app": {"mono": [5.662, 5.477, 5.951], "poly": [6.009, 5.397, 5.630]},
    "ll": {"mono": [2.962, 2.912, 2.913], "poly": [3.634, 3.987, 3.675]},
}

data_build = {
    "name": "spy build -x --timeit",
    "app": {
        "mono": [2.386, 2.037, 2.047, 1.767, 1.937],
        "poly": [2.074, 1.623, 1.802, 2.228, 1.802],
    },
    "ll": {"mono": [1.254, 1.524, 1.228], "poly": [1.371, 1.725, 1.232]},
}

data_build_release = {
    "name": "spy build -x --timeit --release",
    "app": {
        "mono": [1.214, 0.914, 1.233, 0.924, 0.885],
        "poly": [0.901, 0.833, 0.862, 0.916, 0.843],
    },
    "ll": {
        "mono": [0.346, 0.328, 0.427, 0.341, 0.346],
        "poly": [0.282, 0.251, 0.281, 0.287, 0.291],
    },
}

parser = argparse.ArgumentParser()

parser.add_argument(
    "-r", "--refs", nargs="+", help="Git references to compare", required=True
)
parser.add_argument("--ref-names", nargs="?", help="Strings to label the references")
parser.add_argument(
    "-b",
    "--benchmarks",
    nargs="+",
    type=Path,
    help=".SPy files to benchmark",
    required=True,
)
parser.add_argument(
    "-n", "--num-runs", type=int, help="How many times to run each benchmark", default=3
)
parser.add_argument(
    "--timeout",
    type=int,
    help="Max time (in seconds) to reach each benchmark",
    default=120,
)
parser.add_argument("-v", "--verbose", action="store_true")

RunKind = Literal["interp", "build"]


@dataclass
class SingleResult:
    benchfile: Path | str
    ref: str
    kind: RunKind
    reported_time: Decimal
    refname: str = ""
    _raw_stdout: str = ""
    _raw_stderr: str = ""


@contextmanager
def temp_worktree():
    with TemporaryDirectory() as tmp_dir:
        subprocess.run(["git", "worktree", "add", "--detach", tmp_dir])
        try:
            yield tmp_dir
        finally:
            subprocess.run(["git", "worktree", "remove", tmp_dir, "--force"])


pattern = re.compile(r"main\(\): (?P<time>\d+\.\d+) seconds")


def get_time_from_output(inp: str) -> Decimal | None:
    result = re.search(pattern, inp)
    if result is not None:
        return Decimal(result.group("time"))
    return None


def run_benchmarks_in_ref(
    ref: str,
    ref_name: str,
    benchlist: list[Path],
    *,
    num_runs: int,
    timeout: int,
    verbose=False,
) -> list[SingleResult]:
    if verbose:
        output = lambda *a, **k: print(*a, **k)
    else:
        output = lambda *a, **k: None

    with temp_worktree() as tmp_dir:
        subprocess.run(["git", "checkout", ref], cwd=tmp_dir)
        subprocess.run(["uv", "sync", "--extra", "dev"], cwd=tmp_dir)
        subprocess.run(["uv", "run", "make", "-C", "spy/libspy"], cwd=tmp_dir)
        subprocess.run(["uv", "run", "spy", "cleanup"], cwd=tmp_dir)
        print(f"Running tests in {tmp_dir}")

        results = []
        for bench in benchlist:
            print(f"Running benchmark {bench}".center(80, "-"))
            for i in range(num_runs):
                output(f"Interpreter run {i + 1: >3}: ")
                raw_res_interp = subprocess.run(
                    ["uv", "run", "spy", "--timeit", "--no-spyc", str(bench)],
                    cwd=tmp_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                time = get_time_from_output(
                    raw_res_interp.stdout + raw_res_interp.stderr
                )
                results.append(
                    SingleResult(
                        benchfile=bench,
                        ref=ref,
                        kind="interp",
                        reported_time=time,
                        ref_name=ref_name,
                        _raw_stdout=raw_res_interp.stdout,
                        _raw_srderr=raw_res_interp.stderr,
                    )
                )
                output(f"{time} seconds")
                breakpoint()

                output(f"Build run {i + 1: >3}      :   ")
                raw_res_build = subprocess.run(
                    [
                        "uv",
                        "run",
                        "spy",
                        "build",
                        "-x",
                        "--release",
                        "--timeit",
                        "--no-spyc",
                        str(bench),
                    ],
                    cwd=tmp_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                time = get_time_from_output(raw_res_build.stdout + raw_res_build.stderr)
                results.append(
                    SingleResult(
                        bench,
                        "build",
                        get_time_from_output(raw_res_build.stdout),
                        raw_res_build.stdout,
                        raw_res_build.stderr,
                    )
                )
                output(f"{time} seconds")
                breakpoint()
        return results


def print_data(data: list[SingleResult]) -> None:
    kinds = {sr.kind for sr in data}

    for kind in kinds:
        ref_names = {sr.refname for sr in data}
        print(f"{f' {kind} '.center(60, '.')}")

    # TODO more here. What follows was the first draft
    return
    for data in data_interpreter, data_build, data_build_release:
        headers = ["Benchmark", "Applevel Algo", "LowLevel Algo", "Relative Time"]
        table = []
        for label in "mono", "poly":
            mean_app = mean(data["app"].get(label))
            mean_ll = mean(data["ll"].get(label))
            table.append(
                [
                    label,
                    f"{round(mean_app, 4)}s",
                    f"{round(mean_ll, 4)}s",
                    f"{round(100 * mean_ll / mean_app, 2)}%",
                ]
            )
        print(tabulate.tabulate(table, headers=headers))
        print("\n\n")


def main():
    args = parser.parse_args()
    if args.ref_names is not None and len(args.ref_names) != len(args.refs):
        raise argparse.ArgumentError("The number of refs and ref names must be equal")
    if args.ref_names is None:
        args.ref_names = itertools.cycle([None])

    exc_list: list[Exception] = []
    resolved = []
    for p in args.benchmarks:
        if not p.exists():
            exc_list.append(argparse.ArgumentError(f"Path {p} does not exist"))
            continue
        if not p.is_file():
            exc_list.append(
                argparse.ArgumentError(f"Path {p} exists but does not refer to a file")
            )
            continue
        if not p.suffix == ".spy":
            exc_list.append(f"Only .spy files can be benchmarked; got {p}")
            continue
        resolved.append(p.resolve())
    if exc_list:
        raise ExceptionGroup("Encountered errors while gathering benchmarks", exc_list)

    results: list[SingleResult] = []
    for ref, name in zip(args.refs, args.ref_names):
        results.extend(
            run_benchmarks_in_ref(
                ref,
                name,
                benchlist=resolved,
                num_runs=args.num_runs,
                timeout=args.timeout,
                verbose=args.verbose,
            )
        )


if __name__ == "__main__":
    main()
