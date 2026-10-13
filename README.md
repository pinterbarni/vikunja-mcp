# vikunja-mcp

MCP server that exposes a self-hosted Vikunja instance as tools for MCP clients.

Work in progress.

## Setup

You need [uv](https://docs.astral.sh/uv/) installed.

Install Python 3.12 if you don't have it:

```bash
uv python install 3.12
```

Create the virtual environment and install the project with its dev tools:

```bash
uv sync
```

Check that the package imports and print its version:

```bash
uv run python -c "import vikunja_mcp; print(vikunja_mcp.__version__)"
```

## Configuration

Settings are environment variables, or entries in a local `.env` file.

| Variable                  | Required | Default | Purpose                                                                       |
| ------------------------- | -------- | ------- | ----------------------------------------------------------------------------- |
| `VIKUNJA_URL`             | yes      | none    | Base URL of your Vikunja instance. A trailing slash or `/api/v1` is accepted. |
| `VIKUNJA_API_TOKEN`       | yes      | none    | API token used for every Vikunja request. Never logged.                       |
| `VIKUNJA_TIMEOUT_SECONDS` | no       | `10`    | Seconds to wait for Vikunja before giving up. Must be greater than zero.      |

The server does not start if a required variable is missing or invalid.

## Development

### Before you commit ✨

Run all checks (tests, lint, format check, spelling):

```bash
make check
```

Auto-fix lint and formatting issues first if needed:

```bash
make fix
```

Single checks: `make test`, `make lint`, `make format`, `make spell`.

---

Run the tests:

```bash
uv run pytest
```

Check the code for problems (unused imports, bugs, style):

```bash
uv run ruff check .
```

Fix the problems ruff can fix on its own:

```bash
uv run ruff check . --fix
```

Format the code:

```bash
uv run ruff format .
```

Check formatting without changing any file (this is what CI will run):

```bash
uv run ruff format --check .
```

Check spelling in code and docs with [cspell](https://cspell.org/):

```bash
npx cspell "**/*.{py,md,toml,json}"
```

## Project layout

```bash
src/vikunja_mcp/   the package
tests/             tests, run with pytest
pyproject.toml     project metadata and tool settings
cspell.json        spell check settings and project words
```

## Docs

### Project

- The plan, requirements and deployment budget are available in a MD file at the moment, for this project I was planning on writing the documentation only after implementing an MVP.

### Tooling

- [uv](https://docs.astral.sh/uv/): package and environment manager
- [pytest](https://docs.pytest.org/): test runner
- [Ruff](https://docs.astral.sh/ruff/): linter and formatter
- [cspell](https://cspell.org/): spell checker
- [pydantic](https://pydantic.dev/docs/validation/dev/get-started/): data validation library

### Vikunja

- [Vikunja docs](https://vikunja.io/docs/): user and admin guides
- [Vikunja API docs](https://vikunja.io/docs/api-documentation/): REST API reference, also served as Swagger on own instance at `/api/v1/docs`
