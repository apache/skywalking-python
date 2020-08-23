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

> If you want to try out the latest features that are not released yet, please refer to [the guide](docs/FAQ.md#q-how-to-build-from-sources) to build from sources.

```python
from skywalking import agent, config

config.init(collector='127.0.0.1:11800', service='your awesome service')
agent.start()
```

Alternatively, you can also pass the configurations via environment variables (such as `SW_AGENT_NAME`, `SW_AGENT_COLLECTOR_BACKEND_SERVICES`, etc.) so that you don't need to call `config.init`.

All supported environment variables can be found [here](docs/EnvVars.md)

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

with context.new_exit_span(op='https://github.com/apache', peer='localhost:8080') as span:
    span.component = Component.Flask

with context.new_local_span(op='https://github.com/apache') as span:
    span.tag(Tag(key='Singer', val='Nakajima'))
```

### Decorators

```python
from time import sleep

from skywalking import Component
from skywalking.decorators import trace, runnable
from skywalking.trace.context import SpanContext, get_context
from skywalking.trace.ipc.process import SwProcess

@trace()  # the operation name is the method name('some_other_method') by default
def some_other_method():
    sleep(1)


@trace(op='awesome')  # customize the operation name to 'awesome'
def some_method():
    some_other_method()


@runnable() # cross thread propagation
def some_method(): 
    some_other_method()

from threading import Thread 
t = Thread(target=some_method)
t.start()

# When another process is started, agents will also be started in other processes, 
# supporting only the process mode of spawn.
p1 = SwProcess(target=some_method) 
p1.start()
p1.join()


context: SpanContext = get_context()
with context.new_entry_span(op=str('https://github.com/apache/skywalking')) as span:
    span.component = Component.Flask
    some_method()
```

## Contributing

Before submitting a pull request or push a commit, please read our [contributing](CONTRIBUTING.md) and [developer guide](docs/Developer.md).

## FAQs

Check [the FAQ page](docs/FAQ.md) or add the FAQs there.

## License
Apache 2.0
