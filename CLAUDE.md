# SkyWalking Python Agent

Apache SkyWalking Python agent for distributed tracing, metrics, logging, and profiling.

## Project Structure

```
skywalking/              # Main agent package
  __init__.py            # Component, Layer, Kind enums
  config.py              # All config via SW_AGENT_* env vars
  agent/                 # SkyWalkingAgent singleton, queue management, reporter threads
  trace/                 # context.py, span.py, carrier.py, segment.py, tags.py
  plugins/               # ~37 auto-instrumentation plugins (sw_*.py)
  meter/                 # Counter, gauge, histogram, PVM metrics
  log/                   # Structured logging with trace context
  profile/               # Thread/greenlet profiling
  client/                # gRPC/HTTP/Kafka protocol clients (sync + async)
  bootstrap/             # CLI (sw-python), sitecustomize loader, uwsgi hook
  utils/                 # Filters, comparators, atomic refs
  decorators.py          # @trace, @runnable for manual instrumentation
sw_python/               # CLI entry point module
tests/
  unit/                  # Standard pytest unit tests
  plugin/                # Docker-based integration tests per plugin
    base.py              # TestPluginBase with validate() method
    conftest.py          # docker_compose fixture (testcontainers)
    docker-compose.base.yml  # Mock collector + agent base services
    Dockerfile.plugin    # Agent image for plugin testing
    data/                # Data layer plugins (redis, mongo, mysql, etc.)
    http/                # HTTP client plugins (requests, urllib3, httpx, etc.)
    web/                 # Web framework plugins (flask, django, fastapi, etc.)
  e2e/                   # End-to-end tests with SkyWalking infra-e2e
  orchestrator.py        # get_test_vector() for multi-version testing
tools/
  plugin_doc_gen.py      # Auto-generate docs/en/setup/Plugins.md
  config_doc_gen.py      # Auto-generate Configuration.md
```

## Python Version Support

- Declared `>=3.10, <3.15`; CI runs the plugin/unit matrix on Python 3.10 - 3.14.
- The agent requires `grpcio >= 1.83`. The generated protobuf stubs refuse an older grpcio
  at import (`GRPC_GENERATED_VERSION`), so the codegen `grpcio-tools` in the Makefile is
  pinned in lockstep — bumping it raises the runtime floor for every user.

## Build & Development

```bash
make env          # Setup Poetry environment with all extras
make install      # Install with all optional dependencies
make lint         # Run flake8 + pylint
make fix          # Auto-fix style (unify, flynt)
make test         # Full test suite (unit + plugin docker tests)
make doc-gen      # Regenerate Plugins.md + Configuration.md
make package      # Build distribution wheel
make gen          # Generate gRPC protobuf code
```

Uses Poetry for dependency management. Config in `pyproject.toml`.

## Plugin Configuration Options (config.py)

Plugin-specific settings (all via `SW_` env vars):
- `agent_disable_plugins`: comma-separated regex patterns to skip plugins
- `plugin_http_http_params_length_threshold`: max chars for HTTP params (default 1024)
- `plugin_http_ignore_method`: comma-delimited HTTP methods to ignore
- `plugin_sql_parameters_max_length`: max SQL param length (default 0 = disabled)
- `plugin_flask_collect_http_params`, `plugin_django_collect_http_params`, `plugin_fastapi_collect_http_params`, `plugin_sanic_collect_http_params`, `plugin_bottle_collect_http_params`: collect HTTP params per framework
- `plugin_pymongo_trace_parameters` / `plugin_pymongo_parameters_max_length`: MongoDB filter tracing
- `plugin_elasticsearch_trace_dsl`: trace ES DSL
- `plugin_celery_parameters_length`: max Celery param length (default 512)
- `plugin_grpc_ignored_methods`: comma-delimited gRPC methods to ignore

Filter functions: `config.ignore_http_method_check(method)`, `config.ignore_grpc_method_check(method)`

## Agent Lifecycle & Fork Support

`SkyWalkingAgent` (skywalking/agent/__init__.py) has two entry points:

- `start()` — full agent: `config.finalize()` (once per lineage; `finalize_name` is NOT
  idempotent), `log.install()` + `plugins.install()`, then `__bootstrap()` creates the queues,
  the protocol client (the gRPC channel lives here) and the reporter threads.
- `start_prefork_master()` — instrumentation only: everything above EXCEPT queues, protocol
  and threads. Used for the Gunicorn master.

**Never create a gRPC channel before `fork()`.** With grpcio >= 1.80 a channel that survives
`fork()` produces `Kick Failure` stderr spam and can silently deadlock the child inside gRPC's
own at-fork handlers (grpc/grpc#43055, apache/skywalking#13958). So:

- Gunicorn (`sw-python run -p gunicorn`): master instruments only, each forked worker runs the
  full agent via the `os.register_at_fork(after_in_child=...)` hook. The master is not a
  service instance. uWSGI has always worked this way, via its `@postfork` hook.
- `SW_AGENT_ASYNCIO_ENHANCEMENT` has no fork support at all and is rejected under `-p`.
- Explicit `os.fork()` over gRPC is unreliable regardless (reporters enter gRPC independently
  of requests) — document HTTP/Kafka for forking apps.

`agent.started()` reports whether reporting is live in this process. It is False in a prefork
master, where `is_segment_queue_full()` returns True so span creation short-circuits to
`NoopSpan` and `archive_*` drop — otherwise instrumented code running at `--preload` import
time would hit uninitialized queues.

## Context & Carrier API Details

### get_context() Signatures
```python
context.new_entry_span(op: str, carrier: Optional[Carrier] = None, inherit: Optional[Component] = None) -> Span
context.new_exit_span(op: str, peer: str, component: Optional[Component] = None, inherit: Optional[Component] = None) -> Span
context.new_local_span(op: str) -> Span
context.active_span  # property: current topmost active span
context.put_correlation(key, value)  # max 3 elements, 128 chars each
context.get_correlation(key) -> str
```

### Carrier Format
- `Carrier` class with key `sw8`, encodes 8 parts: sample, trace_id, segment_id, span_id, service, instance, endpoint, client_address (all base64 except span_id)
- `SW8CorrelationCarrier` subclass with key `sw8-correlation` for cross-process correlation context
- Iterate carrier items: `for item in carrier: headers[item.key] = item.val`
- `carrier.is_valid` / `carrier.is_suppressed` for validation

### URL Filter Utility
```python
from skywalking.utils.filter import sw_urlparse, sw_traceback
url_param = sw_urlparse(url)  # Returns parsed URL with credentials stripped from netloc
```

## Plugin Development

### Plugin Contract

Every plugin is a module file `skywalking/plugins/sw_<name>.py` with:

```python
# Required module-level attributes
link_vector = ['https://docs.example.com/']
support_matrix = {
    'package-name': {
        '>=3.7': ['1.0', '2.0']  # Python version -> tested lib versions
    }
}
note = """"""

# Required function
def install():
    # Monkey-patch the target library
    ...
```

### Plugin Discovery

- `skywalking/plugins/__init__.py` uses `pkgutil.iter_modules()` to find all `sw_*.py` files
- Checks `agent_disable_plugins` config (regex patterns) to skip disabled plugins
- Calls `pkg_version_check(plugin)` for version validation
- Calls `plugin.install()` to execute monkey-patching

### Span Types & Usage

```python
from skywalking.trace.context import get_context, NoopContext
from skywalking.trace.span import NoopSpan
from skywalking.trace.carrier import Carrier
from skywalking import Layer, Component, config

context = get_context()

# Entry span (incoming request - web frameworks, message consumers)
carrier = Carrier()
for item in carrier:
    item.val = request.headers.get(item.key)
span = context.new_entry_span(op='/path', carrier=carrier)

# Exit span (outgoing call - HTTP clients, DB queries, cache ops)
span = context.new_exit_span(op='Redis/GET', peer='host:port', component=Component.Redis)

# Local span (internal operations)
span = context.new_local_span(op='process')

# All spans used as context managers
with span:
    span.layer = Layer.Http  # Http, Database, Cache, MQ, RPCFramework
    span.component = Component.Flask
    span.tag(TagHttpMethod('GET'))
    # For exit spans: inject carrier into outgoing headers
    carrier = span.inject()
    for item in carrier:
        headers[item.key] = item.val
    # Call original function
    result = original_func()
    span.tag(TagHttpStatusCode(200))
    if error:
        span.error_occurred = True
        span.raised()  # Captures traceback
```

### Instrumentation Patterns

**Pattern A - Method replacement (most common):**
```python
def install():
    from some_lib import SomeClass
    _original = SomeClass.method

    def _sw_method(this, *args, **kwargs):
        with get_context().new_exit_span(...) as span:
            span.layer = Layer.Http
            result = _original(this, *args, **kwargs)
            return result

    SomeClass.method = _sw_method
```

**Pattern B - wrapt.ObjectProxy (for C extensions like psycopg2, mysqlclient):**
```python
import wrapt

class ProxyCursor(wrapt.ObjectProxy):
    def execute(self, query, vars=None):
        with get_context().new_exit_span(...) as span:
            return self.__wrapped__.execute(query, vars)
```

**Pattern C - Async wrappers (aiohttp, httpx, asyncpg):**
```python
def install():
    from aiohttp import ClientSession
    _request = ClientSession._request

    async def _sw_request(this, method, url, **kwargs):
        with get_context().new_exit_span(...) as span:
            carrier = span.inject()
            headers = kwargs.get('headers') or {}
            for item in carrier:
                headers[item.key] = item.val
            kwargs['headers'] = headers
            res = await _request(this, method, url, **kwargs)
            return res

    ClientSession._request = _sw_request
```

**Pattern D - Framework interceptors (gRPC, middleware):**
Use framework-native interceptor/middleware APIs, create spans inside them.

### Tags (`skywalking/trace/tags.py`)

| Category | Tags |
|----------|------|
| HTTP | TagHttpMethod, TagHttpURL, TagHttpStatusCode, TagHttpStatusMsg, TagHttpParams |
| Database | TagDbType, TagDbInstance, TagDbStatement, TagDbSqlParameters |
| Cache | TagCacheType, TagCacheOp, TagCacheCmd, TagCacheKey |
| MQ | TagMqBroker, TagMqTopic, TagMqQueue |
| gRPC | TagGrpcMethod, TagGrpcUrl, TagGrpcStatusCode |
| Celery | TagCeleryParameters |

### Component IDs (`skywalking/__init__.py`)

New plugins need a Component enum entry. IDs 7000+ are Python-specific.
External components (Redis=7, MongoDB=9, etc.) share IDs with other SkyWalking agents.
New Python-specific components increment from the last used ID.

### Noop Pattern

For ignored requests (e.g., filtered HTTP methods):
```python
span = NoopSpan(NoopContext()) if config.ignore_http_method_check(method) \
    else get_context().new_entry_span(op=path, carrier=carrier)
```

## Plugin Testing

### Test Structure

Each plugin test lives in `tests/plugin/{data|http|web}/sw_<name>/`:

```
sw_<name>/
  __init__.py
  test_<name>.py           # Pytest test class
  expected.data.yml        # Expected span snapshot
  docker-compose.yml       # Service definitions
  services/
    __init__.py
    provider.py            # Backend service using the plugin
    consumer.py            # Frontend service making requests
  requirements.txt         # Auto-generated from version param
```

### Test Pattern

```python
from skywalking.plugins.sw_<name> import support_matrix
from tests.orchestrator import get_test_vector
from tests.plugin.base import TestPluginBase

@pytest.fixture
def prepare():
    return lambda *_: requests.get('http://0.0.0.0:9090/endpoint', timeout=5)

class TestPlugin(TestPluginBase):
    @pytest.mark.parametrize('version', get_test_vector(lib_name='<name>', support_matrix=support_matrix))
    def test_plugin(self, docker_compose, version):
        self.validate()
```

### Docker Compose

- Extends `../../docker-compose.base.yml` for collector + agent base image
- Provider runs on port 9091, consumer on 9090
- Services install the plugin lib via `pip install -r /app/requirements.txt`
- Use `sw-python run python3 /app/services/provider.py` to start with agent
- External services (Redis, Kafka, etc.) added as needed with healthchecks
- The mock collector is pinned by image SHA in `docker-compose.base.yml`. Bumping it also
  pulls in validator changes — verify the whole plugin matrix on CI, not just one test.

### Expected Data Format (expected.data.yml)

```yaml
segmentItems:
  - serviceName: provider
    segmentSize: 1
    segments:
      - segmentId: not null
        spans:
          - operationName: /endpoint
            spanId: 0
            parentSpanId: -1
            spanLayer: Http          # Http, Database, Cache, MQ, RPCFramework
            spanType: Entry          # Entry, Exit, Local
            componentId: 7001       # Must match Component enum value
            peer: not null
            tags:
              - key: http.method
                value: GET
            startTime: gt 0
            endTime: gt 0
            skipAnalysis: false
```

Validation operators: `not null`, `gt 0`, `start with`, `end with`, exact string match.

Validation notes:
- Segments and spans are matched by content, and the expected `segmentSize` / span count must
  match exactly; only services named in the expected file are checked.
- `logItems` entries are ORDER-SIGNIFICANT: the collector sorts expected and actual logs by
  their raw body text before comparing pairwise, so a `text: not null` placeholder sorts as
  the literal string `"not null"`. See `sw_loguru`, which pins a log layout to keep the
  ordering deterministic — it is the only test asserting `logItems`.
- `prepare()` fixtures should call `.raise_for_status()`; otherwise an HTTP error passes the
  fixture silently and surfaces later as a confusing empty-data diff.

### Running Tests

```bash
# Build plugin test image first
docker build --build-arg BASE_PYTHON_IMAGE=3.11-slim \
  -t apache/skywalking-python-agent:latest-plugin --no-cache . \
  -f tests/plugin/Dockerfile.plugin

# Run specific plugin test
poetry run pytest -v tests/plugin/web/sw_flask/

# Run all plugin tests
poetry run pytest -v $(bash tests/gather_test_paths.sh)
```

## Checklist for New Plugins

1. Add `skywalking/plugins/sw_<name>.py` with `link_vector`, `support_matrix`, `note`, `install()`
2. Add Component enum entry in `skywalking/__init__.py` (if new Python-specific component)
3. Add component ID in [the main SkyWalking repo](https://github.com/apache/skywalking/blob/master/oap-server/server-starter/src/main/resources/component-libraries.yml)
4. Add library to `pyproject.toml` plugins group: `poetry add <lib> --group plugins`
5. Create test directory: `tests/plugin/{data|http|web}/sw_<name>/`
6. Create test files: `__init__.py`, `test_<name>.py`, `expected.data.yml`, `docker-compose.yml`, `services/`
7. Run `make doc-gen` to regenerate Plugins.md
8. Verify with `make lint`

## All 38 Plugins

Web: sw_flask, sw_django, sw_fastapi, sw_sanic, sw_sanic_v2, sw_tornado, sw_bottle, sw_pyramid, sw_falcon, sw_falcon_v3
HTTP: sw_requests, sw_urllib3, sw_urllib3_v2, sw_urllib_request, sw_aiohttp, sw_httpx, sw_http_server
Database: sw_pymysql, sw_mysqlclient, sw_psycopg, sw_psycopg2, sw_pymongo, sw_elasticsearch, sw_happybase, sw_neo4j, sw_asyncpg
Cache: sw_redis, sw_aioredis
MQ: sw_kafka, sw_rabbitmq, sw_celery, sw_pulsar, sw_confluent_kafka, sw_aiormq, sw_amqp
RPC: sw_grpc, sw_websockets
Other: sw_loguru (logging)

## License Header

All source files require Apache 2.0 license header. See any existing file for the exact format.

## CI

GitHub Actions in `.github/workflows/CI.yaml`:
- License check + lint
- Plugin doc generation check
- Plugin + unit tests: matrix of Python versions x test paths
- E2E tests: gRPC/HTTP/Kafka protocols, profiling scenarios
- Docker image builds for each Python version

## GitHub Actions Allow List

Apache enforces an allow list for third-party GitHub Actions. All third-party actions
must be pinned to an approved SHA from:
https://github.com/apache/infrastructure-actions/blob/main/approved_patterns.yml

## Skills

- `/new-plugin` — Scaffold a complete new instrumentation plugin (code + tests + docker-compose + expected data)
- `/plugin-test` — Build Docker images and run plugin/unit tests locally, mirroring CI
