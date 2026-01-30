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

## Your First Program

To create your first SPy program, create a file called `hello_world.spy` with the following contents:

```py
# hello_world.spy
def main() -> None:
    print("hello world!")
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
