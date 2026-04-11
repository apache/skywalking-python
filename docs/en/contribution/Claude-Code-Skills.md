# Claude Code Skills

This project includes [Claude Code](https://claude.com/claude-code) configuration to assist with development.

## CLAUDE.md

The `CLAUDE.md` file at the project root provides Claude Code with project context:

- **Project structure** — module layout, key files and their purposes
- **Plugin API** — span types, instrumentation patterns (method replacement, wrapt proxy, async wrappers, interceptors), tags, component IDs
- **Context & Carrier API** — `get_context()` signatures, Carrier format, correlation API
- **Plugin configuration options** — all `SW_AGENT_*` plugin settings
- **Testing framework** — Docker-based integration tests, expected data format, test patterns
- **Build commands** — `make env`, `make test`, `make lint`, `make doc-gen`, etc.
- **CI pipeline** — GitHub Actions matrix, Python version coverage
- **GitHub Actions allow list** — Apache enforces pinned SHAs for third-party actions
- **Complete plugin inventory** — all 35 instrumentation plugins by category

## Skills

### `/new-plugin` — Scaffold a New Plugin

Generates all files needed for a new instrumentation plugin:

- **Plugin module** (`skywalking/plugins/sw_<name>.py`) with correct instrumentation pattern based on plugin type (HTTP entry/exit, database, cache, MQ, RPC)
- **Component enum entry** in `skywalking/__init__.py`
- **Test directory** (`tests/plugin/{data|http|web}/sw_<name>/`) with:
  - Test file with parametrized versions
  - Docker Compose configuration
  - Provider and consumer services
  - Expected span data YAML
- Post-generation reminders (component-libraries.yml, UI logo, doc-gen, lint)

Usage: `/new-plugin` and provide the library name, type, and versions to test.

### `/plugin-test` — Run Plugin Tests Locally

Runs the same tests that CI runs, but locally:

- Builds Docker test images for specific Python versions
- Runs unit tests (no Docker needed) or plugin integration tests
- Maps plugin names to test paths
- Supports testing across multiple Python versions by rebuilding the Docker image
- Includes troubleshooting guidance for common failures (proxy issues, container debugging)

Usage: `/plugin-test` and specify the scope (e.g., `flask`, `redis`, `unit`, `all`) and Python version.

**Important**: If you have `http_proxy`/`https_proxy` set, clear them before running plugin tests — the test HTTP requests must reach Docker containers directly.
