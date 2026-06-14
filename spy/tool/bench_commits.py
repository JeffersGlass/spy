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
from pathlib import Path
from statistics import mean
from tempfile import TemporaryDirectory
from typing import Any, Literal

import tabulate

parser = argparse.ArgumentParser()

parser.add_argument(
    "-r", "--refs", nargs="+", help="Git references to compare", required=True
)
parser.add_argument("--ref-names", nargs="*", help="Strings to label the references")
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
parser.add_argument("-v", "--verbose", action="count")

RunKind = Literal["interp", "build"]


@dataclass
class SingleResult:
    benchfile: Path | str
    ref: str
    kind: RunKind
    reported_time: float
    refname: str = ""
    _raw_stdout: str = ""
    _raw_stderr: str = ""


@contextmanager
def temp_worktree(verbose: int = 0):
    with TemporaryDirectory() as tmp_dir:
        subprocess.run(["git", "worktree", "add", "--detach", tmp_dir])
        try:
            yield tmp_dir
        finally:
            subprocess.run(["git", "worktree", "remove", tmp_dir, "--force"])


pattern = re.compile(r"main\(\): (?P<time>\d+\.\d+) seconds")


def get_time_from_output(inp: str) -> float:
    result = re.search(pattern, inp)
    if result is not None:
        return float(result.group("time"))
    return -1.0


def run_in_dir(cmd: list[str], cwd: Path | str, verbose: int = 0):
    if verbose >= 2:
        capture_output = False
    else:
        capture_output = True
    subprocess.run(cmd, cwd=cwd, capture_output=capture_output)


def run_benchmarks_in_ref(
    ref: str,
    refname: str,
    benchlist: list[Path],
    *,
    num_runs: int,
    timeout: int,
    verbose=0,
) -> list[SingleResult]:
    if verbose > 0:
        output = lambda *a, **k: print(*a, **k)
    else:
        output = lambda *a, **k: None

    with temp_worktree() as tmp_dir:
        run_in_dir(["git", "checkout", ref], cwd=tmp_dir, verbose=verbose)
        run_in_dir(["uv", "sync", "--extra", "dev"], cwd=tmp_dir, verbose=verbose)
        run_in_dir(
            ["uv", "run", "make", "-C", "spy/libspy"], cwd=tmp_dir, verbose=verbose
        )
        run_in_dir(["uv", "run", "spy", "cleanup"], cwd=tmp_dir, verbose=verbose)
        output(f"Running tests in {tmp_dir}")

        results = []
        for bench in benchlist:
            output(f"Running benchmark {bench}".center(80, "-"))
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
                        reported_time=time if time else -1,
                        refname=refname,
                        # _raw_stdout=raw_res_interp.stdout,
                        # _raw_stderr=raw_res_interp.stderr,
                    )
                )
                output(f"{time} seconds")

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
                        ref=ref,
                        kind="build",
                        reported_time=get_time_from_output(raw_res_build.stdout),
                        refname=refname,
                        # _raw_stdout=raw_res_build.stdout,
                        # _raw_stderr=raw_res_build.stderr,
                    )
                )
                output(f"{time} seconds")
        return results


def print_data(all_results: list[SingleResult]) -> None:
    kinds = {sr.kind for sr in all_results}

    for execution_kind in kinds:
        # gather all runs of this kind
        k_results = [sr for sr in all_results if sr.kind == execution_kind]
        refnames_in_results = list({sr.refname for sr in k_results})
        benchmarks = {sr.benchfile for sr in k_results}

        headers = ["Benchmark", *refnames_in_results]
        table = []

        for bench in benchmarks:
            line: list[Path | str] = [
                (bench.name if isinstance(bench, Path) else bench)
            ]
            for refname in refnames_in_results:
                ref_results = [sr for sr in k_results if sr.refname == refname]
                times = [sr.reported_time for sr in ref_results if sr.reported_time > 0]
                if times:
                    line.append(f"{round(mean(times), 2)}s")
                    meantime = mean(times)
                else:
                    line.append(f"nil")

            table.append(line)

        print("\n\n")
        print(f"{f' {execution_kind} '.center(60, '.')}")
        print(tabulate.tabulate(table, headers=headers))


def main():
    args = parser.parse_args()
    if args.ref_names is not None and len(args.ref_names) != len(args.refs):
        raise ValueError("The number of refs and ref names must be equal")
    if args.ref_names is None:
        args.ref_names = itertools.cycle(["<refname>"])

    exc_list: list[Exception] = []
    resolved = []
    for p in args.benchmarks:
        if not p.exists():
            exc_list.append(ValueError(f"Path {p} does not exist"))
            continue
        if not p.is_file():
            exc_list.append(ValueError(f"Path {p} exists but does not refer to a file"))
            continue
        if not p.suffix == ".spy":
            exc_list.append(ValueError(f"Only .spy files can be benchmarked; got {p}"))
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

    print_data(results)


if __name__ == "__main__":
    main()
