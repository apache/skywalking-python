---
name: new-plugin
description: Scaffold a new SkyWalking Python instrumentation plugin with all required files (plugin code, tests, docker-compose, expected data, services)
user-invocable: true
---

# New SkyWalking Python Plugin

Generate a complete instrumentation plugin for the SkyWalking Python agent. Ask the user for:

1. **Library name** (e.g., `httpx`, `pymemcache`, `clickhouse-driver`)
2. **Plugin type**: web framework (Entry spans), HTTP client (Exit spans), database (Exit spans), cache (Exit spans), message queue (Entry+Exit spans), RPC (Entry+Exit spans)
3. **Library versions to test** (e.g., `['1.0', '2.0']`)
4. **Minimum Python version** (default `>=3.7`)
5. **External service needed for tests?** (e.g., Redis, MySQL, Kafka — or none for HTTP client plugins)

If the user provides a library name without details, research the library to determine the appropriate type and instrumentation points.

## Files to Generate

### 1. Plugin Module: `skywalking/plugins/sw_<name>.py`

Use the Apache 2.0 license header (copy from any existing plugin file).

Follow these patterns based on plugin type:

**For HTTP Exit plugins** (like `sw_requests.py`):
```python
from skywalking import Layer, Component, config
from skywalking.trace.context import get_context, NoopContext
from skywalking.trace.span import NoopSpan
from skywalking.trace.tags import TagHttpMethod, TagHttpURL, TagHttpStatusCode

link_vector = ['<documentation URL>']
support_matrix = {
    '<pip-package-name>': {
        '>=3.13': ['<version>'],  # pin exact latest patch version (e.g., '4.2.0')
        '>=3.10': ['<older_version>', '<version>'],
    }
}
note = """"""

def install():
    from <library> import <Class>
    _original = <Class>.<method>

    def _sw_method(this, *args, **kwargs):
        # Parse URL/peer from args
        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(method) \
            else get_context().new_exit_span(op=path, peer=netloc, component=Component.<Name>)

        with span:
            carrier = span.inject()
            span.layer = Layer.Http
            # Inject carrier into outgoing headers
            for item in carrier:
                headers[item.key] = item.val
            span.tag(TagHttpMethod(method))
            span.tag(TagHttpURL(url))
            res = _original(this, *args, **kwargs)
            span.tag(TagHttpStatusCode(res.status_code))
            if res.status_code >= 400:
                span.error_occurred = True
            return res

    <Class>.<method> = _sw_method
```

**For Web Entry plugins** (like `sw_flask.py`):
```python
from skywalking import Layer, Component, config
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context, NoopContext
from skywalking.trace.span import NoopSpan
from skywalking.trace.tags import TagHttpMethod, TagHttpURL, TagHttpStatusCode

def install():
    from <framework> import <App>
    _original = <App>.<handler_method>

    def _sw_handler(this, *args, **kwargs):
        req = <get_request>
        carrier = Carrier()
        for item in carrier:
            if item.key.capitalize() in req.headers:
                item.val = req.headers[item.key.capitalize()]

        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(req.method) \
            else get_context().new_entry_span(op=req.path, carrier=carrier, inherit=Component.General)

        with span:
            span.layer = Layer.Http
            span.component = Component.<Name>
            span.peer = f"{remote_addr}:{remote_port}"
            span.tag(TagHttpMethod(req.method))
            span.tag(TagHttpURL(req.url))
            resp = _original(this, *args, **kwargs)
            span.tag(TagHttpStatusCode(resp.status_code))
            if resp.status_code >= 400:
                span.error_occurred = True
            return resp

    <App>.<handler_method> = _sw_handler
```

**For Database/Cache Exit plugins** (like `sw_redis.py`):
```python
from skywalking import Layer, Component
from skywalking.trace.context import get_context
from skywalking.trace.tags import TagDbType, TagDbInstance, TagDbStatement  # or TagCacheType, TagCacheOp, etc.

def install():
    from <library> import <Connection>
    _original = <Connection>.<method>

    def _sw_method(this, *args, **kwargs):
        peer = f'{this.host}:{this.port}'
        with get_context().new_exit_span(op='<DB>/<operation>', peer=peer, component=Component.<Name>) as span:
            span.layer = Layer.Database  # or Layer.Cache
            span.tag(TagDbType('<DB type>'))
            span.tag(TagDbStatement(query))
            res = _original(this, *args, **kwargs)
            return res

    <Connection>.<method> = _sw_method
```

**For MQ plugins** (producer Exit + consumer Entry):
- Producer: new_exit_span, inject carrier into message headers, Layer.MQ
- Consumer: new_entry_span, extract carrier from message headers, Layer.MQ

**For async plugins**: Use `async def` wrappers, `await` the original call.

**For C extension libraries**: Use `wrapt.ObjectProxy` pattern (see `sw_psycopg2.py`).

### 2. Component Enum: `skywalking/__init__.py`

Add a new entry to the `Component` enum. Check the last Python-specific ID (7000+) and increment. Example:
```python
NewLib = 7020  # Next available ID
```

If the component already exists in the SkyWalking ecosystem (check existing enum), reuse that ID.

### 3. Test Directory: `tests/plugin/{data|http|web}/sw_<name>/`

Choose the subdirectory:
- `web/` for web frameworks
- `http/` for HTTP clients
- `data/` for databases, caches, message queues

Create these files:

#### `__init__.py`
Empty file with license header.

#### `test_<name>.py`
```python
from typing import Callable
import pytest
import requests
from skywalking.plugins.sw_<name> import support_matrix
from tests.orchestrator import get_test_vector
from tests.plugin.base import TestPluginBase

@pytest.fixture
def prepare():
    return lambda *_: requests.get('http://0.0.0.0:9090/<endpoint>', timeout=5)

class TestPlugin(TestPluginBase):
    @pytest.mark.parametrize('version', get_test_vector(lib_name='<name>', support_matrix=support_matrix))
    def test_plugin(self, docker_compose, version):
        self.validate()
```

#### `docker-compose.yml`
```yaml
version: '2.1'

services:
  collector:
    extends:
      service: collector
      file: ../../docker-compose.base.yml

  # Add external service if needed (database, cache, MQ broker)
  # <service_name>:
  #   image: <image>
  #   ports: [<port>:<port>]
  #   healthcheck: ...
  #   networks: [beyond]

  provider:
    extends:
      service: agent
      file: ../../docker-compose.base.yml
    ports:
      - 9091:9091
    volumes:
      - .:/app
    command: ['bash', '-c', 'pip install flask && pip install -r /app/requirements.txt && sw-python run python3 /app/services/provider.py']
    depends_on:
      collector:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "bash", "-c", "cat < /dev/null > /dev/tcp/127.0.0.1/9091"]
      interval: 5s
      timeout: 60s
      retries: 120
    environment:
      SW_AGENT_NAME: provider
      SW_AGENT_LOGGING_LEVEL: DEBUG

  consumer:
    extends:
      service: agent
      file: ../../docker-compose.base.yml
    ports:
      - 9090:9090
    volumes:
      - .:/app
    command: ['bash', '-c', 'pip install flask && pip install -r /app/requirements.txt && sw-python run python3 /app/services/consumer.py']
    depends_on:
      collector:
        condition: service_healthy
      provider:
        condition: service_healthy
    environment:
      SW_AGENT_NAME: consumer
      SW_AGENT_LOGGING_LEVEL: DEBUG

networks:
  beyond:
```

Key points:
- Consumer listens on port 9090, provider on 9091
- Consumer calls provider to create cross-process trace
- Use `sw-python run python3` to start with agent instrumentation
- The consumer uses Flask to expose an HTTP endpoint for the test's `prepare()` fixture to hit
- The provider uses the target library (e.g., makes a Redis call, DB query)
- Both install the target library via `pip install -r /app/requirements.txt`

#### `services/provider.py`
Flask app on port 9091 that uses the target library. Example for a data plugin:
```python
if __name__ == '__main__':
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route('/endpoint', methods=['POST', 'GET'])
    def handler():
        import <target_library>
        # Make a call using the target library
        # e.g., client = redis.StrictRedis(host='redis'); client.get('key')
        return jsonify({'status': 'ok'})

    app.run(host='0.0.0.0', port=9091)
```

#### `services/consumer.py`
Flask app on port 9090 that calls the provider:
```python
import requests

if __name__ == '__main__':
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route('/endpoint', methods=['POST', 'GET'])
    def handler():
        res = requests.post('http://provider:9091/endpoint', timeout=5)
        return jsonify(res.json())

    app.run(host='0.0.0.0', port=9090)
```

#### `services/__init__.py`
Empty file with license header.

#### `expected.data.yml`
Define expected spans. Structure depends on plugin type:

For a **data/cache Exit** plugin (consumer -> provider -> external service):
```yaml
segmentItems:
  - serviceName: provider
    segmentSize: 1
    segments:
      - segmentId: not null
        spans:
          - operationName: <DB>/<operation>
            parentSpanId: 0
            spanId: 1
            spanLayer: Database  # or Cache
            startTime: gt 0
            endTime: gt 0
            componentId: <ID>
            spanType: Exit
            peer: <service>:<port>
            skipAnalysis: false
            tags:
              - key: db.type
                value: <type>
              - key: db.statement
                value: <query>
          - operationName: /endpoint
            parentSpanId: -1
            spanId: 0
            spanLayer: Http
            startTime: gt 0
            endTime: gt 0
            componentId: 7001
            spanType: Entry
            peer: not null
            skipAnalysis: false
            tags:
              - key: http.method
                value: POST
              - key: http.url
                value: http://provider:9091/endpoint
              - key: http.status_code
                value: '200'
            refs:
              - parentEndpoint: /endpoint
                networkAddress: 'provider:9091'
                refType: CrossProcess
                parentSpanId: 1
                parentTraceSegmentId: not null
                parentServiceInstance: not null
                parentService: consumer
                traceId: not null
  - serviceName: consumer
    segmentSize: 1
    segments:
      - segmentId: not null
        spans:
          - operationName: /endpoint
            parentSpanId: 0
            spanId: 1
            spanLayer: Http
            startTime: gt 0
            endTime: gt 0
            componentId: 7002
            spanType: Exit
            peer: provider:9091
            skipAnalysis: false
            tags:
              - key: http.method
                value: POST
              - key: http.url
                value: http://provider:9091/endpoint
              - key: http.status_code
                value: '200'
          - operationName: /endpoint
            parentSpanId: -1
            spanId: 0
            spanLayer: Http
            startTime: gt 0
            endTime: gt 0
            componentId: 7001
            spanType: Entry
            peer: not null
            skipAnalysis: false
            tags:
              - key: http.method
                value: GET
              - key: http.url
                value: http://0.0.0.0:9090/endpoint
              - key: http.status_code
                value: '200'
```

Important notes for expected data:
- Spans within a segment are ordered **child-first** (highest spanId first)
- Entry spans have `parentSpanId: -1`
- Exit spans reference the entry span as parent
- Cross-process refs link consumer exit span to provider entry span
- `componentId` must match the Component enum value exactly
- Consumer's exit span uses Requests component (7002) since it calls via `requests.post()`
- Consumer's entry span uses Flask component (7001) since it receives via Flask

### 4. Update `pyproject.toml`

Add the library to `[tool.poetry.group.plugins.dependencies]`:
```bash
poetry add <library> --group plugins
```

### 5. Regenerate Docs

```bash
make doc-gen
```

### 6. Lint Check

```bash
make lint
```

## Post-Generation Reminders

After generating all files, remind the user:
1. A new component ID may need to be registered in the [main SkyWalking repo's component-libraries.yml](https://github.com/apache/skywalking/blob/master/oap-server/server-starter/src/main/resources/component-libraries.yml) and a logo added to the [UI repo](https://github.com/apache/skywalking-booster-ui/tree/main/src/assets/img/technologies)
2. Run `make doc-gen` to regenerate Plugins.md
3. Run `make lint` to verify code style
4. Test locally: build the Docker image and run `poetry run pytest -v tests/plugin/<category>/sw_<name>/`
5. All files need the Apache 2.0 license header
