# Useful Commands

## From within /docs:
Editable installs are a bit borked... to make them better:
```sh
rm -rf ../.venv && uv pip install -e ../../mkdocs-spy/ && uv sync --all-groups --all-extras --refresh && uv run mkdocs serve
```