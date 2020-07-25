# SkyWalking Python Agent

<img src="http://skywalking.apache.org/assets/logo.svg" alt="Sky Walking logo" height="90px" align="right" />

**SkyWalking-Python**: The Python Agent for Apache SkyWalking, which provides the native tracing abilities for Python project.

**SkyWalking**: an APM(application performance monitor) system, especially designed for
microservices, cloud native and container-based (Docker, Kubernetes, Mesos) architectures.

[![GitHub stars](https://img.shields.io/github/stars/apache/skywalking-python.svg?style=for-the-badge&label=Stars&logo=github)](https://github.com/apache/skywalking-python)
[![Twitter Follow](https://img.shields.io/twitter/follow/asfskywalking.svg?style=for-the-badge&label=Follow&logo=twitter)](https://twitter.com/AsfSkyWalking)


[![Build](https://github.com/apache/skywalking-python/workflows/Build/badge.svg?branch=master)](https://github.com/apache/skywalking-python/actions?query=branch%3Amaster+event%3Apush+workflow%3A%22Build%22)

## Install

### From Pypi

The Python agent module is published to [Pypi](https://pypi.org/project/apache-skywalking/), from where you can use `pip` to install:

```shell
# Install the latest version
pip install apache-skywalking

# Install a specific version x.y.z
# pip install apache-skywalking==x.y.z
pip install apache-skywalking==0.1.0  # For example, install version 0.1.0 no matter what the latest version is
```

### From Source Codes

Refer to the [FAQ](docs/FAQ.md#q-how-to-build-from-sources).

## Set up Python Agent

SkyWalking Python SDK requires SkyWalking 8.0+ and Python 3.5+.

> If you want to try out the latest features that're not released yet, please refer to [the guide](docs/FAQ.md#q-how-to-build-from-sources) to build from sources.

```python
from skywalking import agent, config

config.init(collector='127.0.0.1:11800', service='your awesome service')
agent.start()
```

Alternatively, you can also pass the configurations via environment variables and you don't need to call `config.init`.

The supported environment variables are as follows:

Environment Variable | Description | Default
| :--- | :--- | :--- |
| `SW_AGENT_NAME` | The name of the Python service | `Python Service Name` |
| `SW_AGENT_INSTANCE` | The name of the Python service instance | Randomly generated |
| `SW_AGENT_COLLECTOR_BACKEND_SERVICES` | The backend OAP server address | `127.0.0.1:11800` |
| `SW_AGENT_PROTOCOL` | The protocol to communicate with the backend OAP, `http` or `grpc`, **we highly suggest using `grpc` in production as it's well optimized than `http`** | `grpc` |
| `SW_AGENT_AUTHENTICATION` | The authentication token to verify that the agent is trusted by the backend OAP, as for how to configure the backend, refer to [the yaml](https://github.com/apache/skywalking/blob/4f0f39ffccdc9b41049903cc540b8904f7c9728e/oap-server/server-bootstrap/src/main/resources/application.yml#L155-L158). | not set |
| `SW_AGENT_LOGGING_LEVEL` | The logging level, could be one of `CRITICAL`, `FATAL`, `ERROR`, `WARN`(`WARNING`), `INFO`, `DEBUG` | `INFO` |
| `SW_AGENT_DISABLE_PLUGINS` | The name patterns in CSV pattern, plugins whose name matches one of the pattern won't be installed | `''` |
| `SW_MYSQL_TRACE_SQL_PARAMETERS` | Indicates whether to collect the sql parameters or not | `False` |
| `SW_MYSQL_SQL_PARAMETERS_MAX_LENGTH` | The maximum length of the collected parameter, parameters longer than the specified length will be truncated | `512` |
| `SW_IGNORE_SUFFIX` | If the operation name of the first span is included in this set, this segment should be ignored. | `.jpg,.jpeg,.js,.css,.png,.bmp,.gif,.ico,.mp3,.mp4,.html,.svg` |
| `SW_FLASK_COLLECT_HTTP_PARAMS`| This config item controls that whether the Flask plugin should collect the parameters of the request.| `false` |
| `SW_DJANGO_COLLECT_HTTP_PARAMS`| This config item controls that whether the Django plugin should collect the parameters of the request.| `false` |
| `SW_HTTP_PARAMS_LENGTH_THRESHOLD`| When `COLLECT_HTTP_PARAMS` is enabled, how many characters to keep and send to the OAP backend, use negative values to keep and send the complete parameters, NB. this config item is added for the sake of performance.  | `1024` |


## Supported Libraries

There're some built-in plugins that support automatic instrumentation of Python libraries, the complete lists are as follow:

Library | Plugin Name
| :--- | :--- |
| [http.server](https://docs.python.org/3/library/http.server.html) | `sw_http_server` |
| [urllib.request](https://docs.python.org/3/library/urllib.request.html) | `sw_urllib_request` |
| [requests](https://requests.readthedocs.io/en/master/) | `sw_requests` |
| [Flask](https://flask.palletsprojects.com/en/1.1.x/) | `sw_flask` |
| [PyMySQL](https://pymysql.readthedocs.io/en/latest/) | `sw_pymysql` |
| [Django](https://www.djangoproject.com/) | `sw_django` |
| [redis-py](https://github.com/andymccurdy/redis-py/) | `sw_redis` |
| [kafka-python](https://kafka-python.readthedocs.io/en/master/) | `sw_kafka` |
| [tornado](https://www.tornadoweb.org/en/stable/) | `sw_tornado` |

## API

Apart from [the libraries](#supported-libraries) that can be instrumented automatically, we also provide some APIs to enable manual instrumentation.

### Create Spans

The code snippet below shows how to create entry span, exit span and local span.

```python
from skywalking import Component
from skywalking.trace.context import SpanContext, get_context
from skywalking.trace.tags import Tag

context: SpanContext = get_context()  # get a tracing context
# create an entry span, by using `with` statement,
# the span automatically starts/stops when entering/exiting the context
with context.new_entry_span(op='https://github.com/apache') as span:
    span.component = Component.Flask
# the span automatically stops when exiting the `with` context

with context.new_exit_span(op='https://github.com/apache', peer='localhost:8080') as span:
    span.component = Component.Flask

with context.new_local_span(op='https://github.com/apache') as span:
    span.tag(Tag(key='Singer', val='Nakajima'))
```

### Decorators

```python
from time import sleep

from skywalking import Component
from skywalking.decorators import trace
from skywalking.trace.context import SpanContext, get_context

@trace()  # the operation name is the method name('some_other_method') by default
def some_other_method():
    sleep(1)


@trace(op='awesome')  # customize the operation name to 'awesome'
def some_method():
    some_other_method()


context: SpanContext = get_context()
with context.new_entry_span(op=str('https://github.com/apache/skywalking')) as span:
    span.component = Component.Flask
    some_method()
```

## FAQs

Check [the FAQ page](docs/FAQ.md) or add the FAQs there.

## For Developers

### Steps to get an operational virtual environment:

1. `git clone https://github.com/apache/skywalking-python.git`
2. `cd skywalking-python/tools/env` (*make sure you actually go into the directory since the scripts use relative paths*)
3. Run the script for your relevant OS to create a virtual environment folder in the project root (*skywalking-python/venv*) and install all the necessary requirements

**Make sure that when the `python` command is executed on your workstation, the binary it references is python 3.5 or newer!**

### Steps after contributing

If your PR introduces the need for a new non-standard library which needs to be pulled via pip or if it removes the need for a previously-used library:
1. navigate to `/path/to/skywalking/agent/tools/env`
2. Execute the `build_requirements` script relevant to your OS.
3. Double check the `requirements.txt` file in the project root to ensure that the changes have been reflected. 

## License
Apache 2.0
