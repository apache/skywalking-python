# Apache SkyWalking Python Agent

[![SkyWalking](https://skyapmtest.github.io/page-resources/SkyAPM/skyapm.png)](https://github.com/apache/skywalking)

[![Twitter Follow](https://img.shields.io/twitter/follow/asfskywalking.svg?style=for-the-badge&label=Follow&logo=twitter)](https://twitter.com/AsfSkyWalking)

[**SkyWalking**](https://github.com/apache/skywalking) Python Agent provides the native tracing abilities for Python project. 

## Set up Python Agent

```python
from skywalking import agent, config

config.init(collector='127.0.0.1:11800', service='your awesome service')
agent.init_and_start()
```

## Supported Libraries

There're some built-in plugins that support automatic instrumentation of Python libraries, the complete lists are as follow:

- Http
  - [http.server](https://docs.python.org/3/library/http.server.html)
  - [urllib.request](https://docs.python.org/3/library/urllib.request.html)

## API

Apart from [the libraries](#supported-libraries) that can be instrumented automatically, we also provide some APIs to enable manual instrumentation.

### Create Spans

```python
from skywalking import Component
from skywalking.trace.context import SpanContext, get_context

context: SpanContext = get_context()  # get a tracing context
# create an entry span, by using `with` statement,
# the span automatically starts/stops when entering/exiting the context
with context.new_entry_span(op=str('https://github.com/apache')) as span:
    span.component = Component.Http
# the span automatically stops when exiting the `with` context
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
with context.new_entry_span(op=str('https://github.com/apache/skywalking')) as s1:
    s1.component = Component.Http
    some_method()
```

## License
Apache 2.0
