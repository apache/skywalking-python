# SkyWalking Python Instrumentation API

Apart from the [supported libraries](../Plugins.md) that can be instrumented automatically, 
SkyWalking also provides some APIs to enable manual instrumentation.

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