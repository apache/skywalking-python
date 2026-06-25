---
name: plugin-test
description: Build Docker test images and run SkyWalking Python plugin/unit/e2e tests locally, mirroring the CI pipeline
user-invocable: true
---

# Run Plugin Tests Locally

This skill runs the same tests that CI runs, but locally. Ask the user what they want to test, or infer from recent changes.

## Options

The user can specify:
- **Scope**: `all`, `unit`, a plugin name (e.g., `flask`, `redis`), a category (`data`, `http`, `web`), or `e2e`
- **Python version**: e.g., `3.11` (default: `3.11-slim` for Docker image)
- **Rebuild image**: whether to rebuild the Docker image (default: only if not already built)

If the user just says `/plugin-test` with no args, ask what to test.

## Prerequisites Check

Before running tests, verify:
```bash
# Check Docker is running
docker info > /dev/null 2>&1 || echo "ERROR: Docker is not running"

# Check Poetry is available
poetry --version || echo "ERROR: Poetry not found, run 'make poetry'"

# Check if environment is set up
poetry env info > /dev/null 2>&1 || echo "WARNING: Poetry env not set up, will run 'make env'"
```

If prerequisites fail, help the user fix them before proceeding.

## Step 1: Setup Environment (if needed)

```bash
make env
```

This installs Poetry and all dependencies including dev and plugin groups.

## Step 2: Build Plugin Test Docker Image

The plugin test image must be built before running any plugin integration tests (not needed for unit tests).

```bash
# Default Python version
docker build --build-arg BASE_PYTHON_IMAGE=3.11-slim \
  -t apache/skywalking-python-agent:latest-plugin --no-cache \
  . -f tests/plugin/Dockerfile.plugin
```

To test with a specific Python version:
```bash
docker build --build-arg BASE_PYTHON_IMAGE=3.12-slim \
  -t apache/skywalking-python-agent:latest-plugin --no-cache \
  . -f tests/plugin/Dockerfile.plugin
```

**Important**: The image tag is always `apache/skywalking-python-agent:latest-plugin` — this is what docker-compose files reference. Rebuilding with a different Python version replaces it.

### Testing Multiple Python Versions

The Python version **inside the Docker container** (not the host) determines what Python the plugin runs under. To test multiple versions, rebuild the image for each:

```bash
# Test with Python 3.11
docker build --build-arg BASE_PYTHON_IMAGE=3.11-slim \
  -t apache/skywalking-python-agent:latest-plugin --no-cache . \
  -f tests/plugin/Dockerfile.plugin
poetry run pytest -v tests/plugin/web/sw_flask/

# Then test with Python 3.13
docker build --build-arg BASE_PYTHON_IMAGE=3.13-slim \
  -t apache/skywalking-python-agent:latest-plugin --no-cache . \
  -f tests/plugin/Dockerfile.plugin
poetry run pytest -v tests/plugin/web/sw_flask/
```

CI does this as a matrix (builds images for each Python version in parallel, then runs all tests against each). Locally, you rebuild and re-run sequentially.

**Available Python base images**: `3.9-slim`, `3.10-slim`, `3.11-slim`, `3.12-slim`, `3.13-slim`, `3.14-slim`

Check if image already exists:
```bash
docker images apache/skywalking-python-agent:latest-plugin --format "{{.ID}} {{.CreatedAt}}"
```

If it exists and is recent, ask the user if they want to rebuild or which Python version to use (rebuilding takes ~1-2 minutes).

## Step 3: Run Tests

### Unit Tests (no Docker needed)
```bash
poetry run pytest -v tests/unit/
```

### Single Plugin Test
Map the plugin name to its test path:
- Web frameworks: `tests/plugin/web/sw_<name>/`
- HTTP clients: `tests/plugin/http/sw_<name>/`
- Data stores: `tests/plugin/data/sw_<name>/`

```bash
poetry run pytest -v tests/plugin/web/sw_flask/
poetry run pytest -v tests/plugin/data/sw_redis/
poetry run pytest -v tests/plugin/http/sw_requests/
```

### Plugin Category
```bash
poetry run pytest -v tests/plugin/data/    # All data plugins
poetry run pytest -v tests/plugin/http/    # All HTTP plugins
poetry run pytest -v tests/plugin/web/     # All web plugins
```

### All Tests
```bash
poetry run pytest -v tests/unit/ tests/plugin/data/ tests/plugin/http/ tests/plugin/web/
```

### E2E Tests
E2E tests need a separate Docker image and use SkyWalking infra-e2e:
```bash
# Build E2E image
docker build --build-arg BASE_PYTHON_IMAGE=3.11-slim \
  -t apache/skywalking-python-agent:latest-e2e --no-cache \
  . -f tests/e2e/base/Dockerfile.e2e

# E2E tests use infra-e2e framework, not pytest directly
# They are defined in tests/e2e/case/*/e2e.yaml
```

Note: E2E tests require the `e2e` CLI tool from SkyWalking infra-e2e. They are typically only run in CI. Inform the user if they ask for E2E.

## Version Format in support_matrix

Use `.*` wildcard to always test the **latest patch** of each minor version:
```python
support_matrix = {
    'falcon': {
        '>=3.13': ['4.*'],         # latest falcon 4.x
        '>=3.10': ['3.1.*', '4.*'],
    }
}
```

- `'4.*'` → pip installs `falcon==4.*` → latest 4.x (e.g., 4.2.0 today, 4.3.0 when released)
- `'4.2.*'` → pip installs `falcon==4.2.*` → latest 4.2.x patch
- `'4.2'` → pip installs `falcon==4.2` → always 4.2.0 (misses patches)

**Convention**: use `major.*` (e.g., `'4.*'`) when the plugin supports the whole major version, or `minor.*` (e.g., `'3.11.*'`) when only specific minors are tested. This keeps CI testing fresh and the Plugins.md doc meaningful.

## Step 4: Interpret Results

### Success
All tests pass with green output. Report the summary.

### Failure - Docker Compose Timeout
```
Wait time exceeded 150 secs
```
This means services didn't start. Check:
1. Is Docker running with enough resources?
2. Is port 9090/9091/12800/19876 already in use? (`lsof -i :9090`)
3. Check Docker logs: `docker compose -f tests/plugin/<category>/sw_<name>/docker-compose.yml logs`

### Failure - Validation Mismatch
The test prints a diff between expected and actual span data. Common causes:
- Wrong `componentId` in expected.data.yml
- Missing or extra spans
- Tag values don't match
- Operation name mismatch

### Failure - Import/Install Error
Plugin library failed to install in Docker. Check:
- Library version compatibility with Python version
- requirements.txt content in the test directory
- Docker compose command for the service

### Failure - Permanent 502 / Empty Segments
**IMPORTANT: Check your HTTP proxy first!** If `http_proxy` or `https_proxy` environment variables are set, ALL test HTTP requests (prepare, validate) go through the proxy instead of reaching Docker containers directly. This causes 502 responses and empty segment data.

```bash
# Check for proxy
echo $http_proxy $https_proxy

# Run tests without proxy
export http_proxy="" https_proxy="" no_proxy="*" NO_PROXY="*"
poetry run pytest -v tests/plugin/web/sw_flask/
```

If still failing after clearing proxy:
- Check container logs: `docker logs sw_<name>-consumer-1`
- Look for whether the service actually started
- Debug in foreground: `docker compose -f <path>/docker-compose.yml up`
- Check ports: `lsof -i :9090 -i :9091 -i :12800`

## Plugin Name to Test Path Mapping

| Plugin | Test Path |
|--------|-----------|
| flask | tests/plugin/web/sw_flask/ |
| django | tests/plugin/web/sw_django/ |
| fastapi | tests/plugin/web/sw_fastapi/ |
| sanic | tests/plugin/web/sw_sanic/ |
| tornado | tests/plugin/web/sw_tornado/ |
| bottle | tests/plugin/web/sw_bottle/ |
| pyramid | tests/plugin/web/sw_pyramid/ |
| falcon | tests/plugin/web/sw_falcon/ |
| grpc | tests/plugin/web/sw_grpc/ |
| requests | tests/plugin/http/sw_requests/ |
| urllib3 | tests/plugin/http/sw_urllib3/ |
| aiohttp | tests/plugin/http/sw_aiohttp/ |
| httpx | tests/plugin/http/sw_httpx/ |
| http | tests/plugin/http/sw_http/ |
| http_wsgi | tests/plugin/http/sw_http_wsgi/ |
| websockets | tests/plugin/http/sw_websockets/ |
| redis | tests/plugin/data/sw_redis/ |
| pymongo | tests/plugin/data/sw_pymongo/ |
| pymysql | tests/plugin/data/sw_pymysql/ |
| mysqlclient | tests/plugin/data/sw_mysqlclient/ |
| psycopg | tests/plugin/data/sw_psycopg/ |
| psycopg2 | tests/plugin/data/sw_psycopg2/ |
| elasticsearch | tests/plugin/data/sw_elasticsearch/ |
| kafka | tests/plugin/data/sw_kafka/ |
| rabbitmq | tests/plugin/data/sw_rabbitmq/ |
| pulsar | tests/plugin/data/sw_pulsar/ |
| neo4j | tests/plugin/data/sw_neo4j/ |
| happybase | tests/plugin/data/sw_happybase/ |
| loguru | tests/plugin/data/sw_loguru/ |

## Useful Debug Commands

```bash
# Check what containers are running during a test
docker ps

# Check container logs for a stuck test
docker compose -f tests/plugin/<category>/sw_<name>/docker-compose.yml logs

# Clean up orphaned containers from failed tests
docker compose -f tests/plugin/<category>/sw_<name>/docker-compose.yml down --remove-orphans

# Check what the mock collector received (while containers are running)
curl http://localhost:12800/receiveData

# Validate expected data manually
curl -X POST http://localhost:12800/dataValidate -d @tests/plugin/<category>/sw_<name>/expected.data.yml

# Check if ports are in use
lsof -i :9090 -i :9091 -i :12800 -i :19876

# Run with verbose output
poetry run pytest -v -s tests/plugin/web/sw_flask/
```
