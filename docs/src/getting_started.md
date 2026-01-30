## Getting SPy

Clone to spy repository: 

```sh 
git clone https://github.com/spylang/spy
cd spy
```

Install spy into a virtual environment using a method of your choice; two options are outlined here.

=== "pip"
    ```sh
    python -m venv .venv
    source ./.venv/bin/activate # or similar for your flavor of shell
    python -m pip install
    ```
=== "uv"
    ```sh
    uv sync
    ```

## Hello World

To create your first SPy program, create a file called `hello_world.spy` with the following contents:

```py
# hello_world.spy
def main() -> None:
    say_hi("world")

def say_hi(name: str) -> None:
    print("hello " + name + "!")
```

Save the file, then run it:

=== "venv"
    ```sh
    python -m spy hello_world.spy
    ```
=== "uv"
    ```sh
    uv run spy hello_world.spy
    ```

```
# result
hello world!
```

### Things to Note:

Functions in SPy must be fully type-annotated [as in PEP484](https://peps.python.org/pep-0484/).

SPy programs to be executed must have a `main` function which accepts no arguments and returns None.

SPy is not CPython; not all operations are supported. See the [SPy Roadmap](https://github.com/spylang/spy/blob/main/ROADMAP.md) for a sense of what's upcoming to be implemented.

## Fibonacci - Compilation

For a more involved example, consider this simble fibonacci program:

```py
#fibo.spy
def fibo(n: int) -> int:
    if n <= 1:
        return n
    else:
        return fibo(n-1) + fibo(n-2)

def main() -> None:
   print(fibo(20))
```

Let's see how long it takes this program to run in the SPy interpreter

=== "venv"
    ```bash
    python -m spy fibo.spy --timeit
    ```
=== "uv"
    ```bash
    uv run spy fibo.spy --timeit
    ```

```
# result
6765
main(): 2.762 seconds # Your machine may vary
```

But SPy programs can be compiled to C code, and built for the current machine, as well as for WASM and Emscripten targets. Let's try compiling this code with the `build` subcommand, and run it afterward by adding the `-x` flag:

=== "venv"
    ```bash
    python -m spy build -x fibo.spy --timeit
    ```
=== "uv"
    ```bash
    uv run spy build -x fibo.spy --timeit
    ```

```
# result
6765
main(): 0.003 seconds
```

Quite the speedup!