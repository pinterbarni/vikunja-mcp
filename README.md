# vikunja-mcp

MCP server that exposes a self-hosted Vikunja instance as tools for MCP clients.

Work in progress.

## Setup

You need [uv](https://docs.astral.sh/uv/) installed.

Install Python 3.12 if you don't have it:

```bash
uv python install 3.12
```

Create the virtual environment and install the project:

```bash
uv sync
```

Check that the package imports and print its version:

```bash
uv run python -c "import vikunja_mcp; print(vikunja_mcp.__version__)"
```

## Spell check

Check spelling in code and docs with [cspell](https://cspell.org/):

```bash
npx cspell "**/*.{py,md,toml,json}"
```
