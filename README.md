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
# Install the latest version, using the default gRPC protocol to report data to OAP
pip install "apache-skywalking"

# Install the latest version, using the http protocol to report data to OAP
pip install "apache-skywalking[http]"

# Install the latest version, using the kafka protocol to report data to OAP
pip install "apache-skywalking[kafka]"

# Install a specific version x.y.z
# pip install apache-skywalking==x.y.z
pip install apache-skywalking==0.1.0  # For example, install version 0.1.0 no matter what the latest version is
```

### From Docker Hub

SkyWalking Python agent provides convenient dockerfile and images for easy integration utilizing its auto-bootstrap
capability. You can build your Python application image based on our agent-enabled Python images and start
your applications with SkyWalking agent enabled for you. Please refer to our 
[dockerfile guide](docker/README.md) for further instructions on building and configurations.

### From Source Codes

Refer to the [FAQ](docs/FAQ.md#q-how-to-build-from-sources).

## Set up Python Agent

SkyWalking Python SDK requires SkyWalking 8.0+ and Python 3.5+.

> If you want to try out the latest features that are not released yet, please refer to [the guide](docs/FAQ.md#q-how-to-build-from-sources) to build from sources.

By default, SkyWalking Python agent uses gRPC protocol to report data to SkyWalking backend,
in SkyWalking backend, the port of gRPC protocol is `11800`, and the port of HTTP protocol is `12800`,
you should configure `collector_address` (or environment variable `SW_AGENT_COLLECTOR_BACKEND_SERVICES`)
according to the protocol you want.

### Non-intrusive integration (CLI)

SkyWalking Python agent supports running and attaching to your awesome applications without adding any code to your
project. The package installation comes with a new command-line script named `sw-python`, which you can use to run your Python-based
applications and programs in the following manner `sw-python run python abc.py` or `sw-python run program arg0 arg1` 

Please do read the [CLI Guide](docs/CLI.md) for a detailed introduction to this new feature before using in production.

You can always fall back to our traditional way of integration as introduced below, 
which is by importing SkyWalking into your project and starting the agent.

### Report data via gRPC protocol (Default)

For example, if you want to use gRPC protocol to report data, configure `collector_address`
(or environment variable `SW_AGENT_COLLECTOR_BACKEND_SERVICES`) to `<oap-ip-or-host>:11800`,
such as `127.0.0.1:11800`:

```python
from skywalking import agent, config

config.init(collector_address='127.0.0.1:11800', service_name='your awesome service')
agent.start()
```

### Report data via HTTP protocol

However, if you want to use HTTP protocol to report data, configure `collector_address`
(or environment variable `SW_AGENT_COLLECTOR_BACKEND_SERVICES`) to `<oap-ip-or-host>:12800`,
such as `127.0.0.1:12800`:

> Remember you should install `skywalking-python` with extra requires `http`, `pip install "apache-skywalking[http]`.

```python
from skywalking import agent, config

config.init(collector_address='127.0.0.1:12800', service_name='your awesome service')
agent.start()
```

### Report data via Kafka protocol

Finally, if you want to use Kafka protocol to report data, configure `kafka_bootstrap_servers`
(or environment variable `SW_KAFKA_REPORTER_BOOTSTRAP_SERVERS`) to `kafka-brokers`,
such as `127.0.0.1:9200`:

> Remember you should install `skywalking-python` with extra requires `kafka`, `pip install "apache-skywalking[kafka]`.

```python
from skywalking import agent, config

config.init(kafka_bootstrap_servers='127.0.0.1:9200', service_name='your awesome service')
agent.start()
```

Alternatively, you can also pass the configurations via environment variables (such as `SW_AGENT_NAME`, `SW_AGENT_COLLECTOR_BACKEND_SERVICES`, etc.) so that you don't need to call `config.init`.

All supported environment variables can be found [here](docs/EnvVars.md)

## Report logs with Python Agent

The Python agent is capable of reporting collected logs to the backend(SkyWalking OAP), enabling Log & Trace Correlation.

Please refer to the [Log Reporter Doc](docs/LogReporter.md) for a detailed guide.

## Supported Libraries

There are some built-in plugins (such as `http.server`, `Flask`, `Django` etc.) that support automatic instrumentation of Python libraries, the complete lists can be found [here](docs/Plugins.md)

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

class TagSinger(Tag):
    key = 'Singer'

with context.new_exit_span(op='https://github.com/apache', peer='localhost:8080', component=Component.Flask) as span:
    span.tag(TagSinger('Nakajima'))

with context.new_local_span(op='https://github.com/apache') as span:
    span.tag(TagSinger('Nakajima'))
```

### Decorators

```python
from time import sleep

from skywalking import Component
from skywalking.decorators import trace, runnable
from skywalking.trace.context import SpanContext, get_context

@trace()  # the operation name is the method name('some_other_method') by default
def some_other_method():
    sleep(1)


@trace(op='awesome')  # customize the operation name to 'awesome'
def some_method():
    some_other_method()


@trace(op='async_functions_are_also_supported')
async def async_func():
    return 'asynchronous'


@trace()
async def async_func2():
    return await async_func()


@runnable() # cross thread propagation
def some_method():
    some_other_method()

from threading import Thread
t = Thread(target=some_method)
t.start()


context: SpanContext = get_context()
with context.new_entry_span(op=str('https://github.com/apache/skywalking')) as span:
    span.component = Component.Flask
    some_method()
```

## Contact Us
* Submit [an issue](https://github.com/apache/skywalking/issues/new) by using [Python] as title prefix.
* Mail list: **dev@skywalking.apache.org**. Mail to `dev-subscribe@skywalking.apache.org`, follow the reply to subscribe the mail list.
* Join `skywalking` channel at [Apache Slack](http://s.apache.org/slack-invite). If the link is not working, find the latest one at [Apache INFRA WIKI](https://cwiki.apache.org/confluence/display/INFRA/Slack+Guest+Invites).
* Twitter, [ASFSkyWalking](https://twitter.com/ASFSkyWalking)

## Contributing

Before submitting a pull request or push a commit, please read our [contributing](CONTRIBUTING.md) and [developer guide](docs/Developer.md).

## FAQs

Check [the FAQ page](docs/FAQ.md) or add the FAQs there.

## License
Apache 2.0
