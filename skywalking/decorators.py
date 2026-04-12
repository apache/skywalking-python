#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import inspect
from functools import wraps
from typing import List

from skywalking import Layer, Component
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag


def trace(
        op: str = None,
        layer: Layer = Layer.Unknown,
        component: Component = Component.Unknown,
        tags: List[Tag] = None,
):
    def decorator(func):
        _op = op or func.__name__

        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                context = get_context()
                span = context.new_local_span(op=_op)
                span.layer = layer
                span.component = component
                if tags:
                    for tag in tags:
                        span.tag(tag)
                with span:
                    return await func(*args, **kwargs)

            return wrapper

        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                context = get_context()
                span = context.new_local_span(op=_op)
                span.layer = layer
                span.component = component
                if tags:
                    for tag in tags:
                        span.tag(tag)
                with span:
                    return func(*args, **kwargs)

            return wrapper

    return decorator


class _RunnableWrapper:
    """Wrapper returned by @runnable. Call continue_tracing() on the parent thread
    to capture the current trace context, then pass the result as Thread target."""

    def __init__(self, func, op, layer, component, tags):
        self._func = func
        self._op = op
        self._layer = layer
        self._component = component
        self._tags = tags
        # Capture snapshot at decoration time — supports inline @runnable usage
        self._snapshot = get_context().capture()
        # Preserve original function attributes
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.__module__ = getattr(func, '__module__', None)
        self.__wrapped__ = func

    def __call__(self, *args, **kwargs):
        """Direct call — creates a local span with cross-thread propagation
        using the snapshot captured at decoration time (inline @runnable pattern)."""
        context = get_context()
        with context.new_local_span(op=self._op) as span:
            if self._snapshot is not None:
                context.continued(self._snapshot)
            span.layer = self._layer
            span.component = self._component
            if self._tags:
                for tag in self._tags:
                    span.tag(tag)
            return self._func(*args, **kwargs)

    def continue_tracing(self):
        """Capture the current trace context snapshot on the calling thread.
        Returns a callable to be used as Thread target that will propagate
        the trace context to the child thread via CrossThread reference."""
        snapshot = get_context().capture()

        def _continued_wrapper(*args, **kwargs):
            context = get_context()
            with context.new_local_span(op=self._op) as span:
                if snapshot is not None:
                    context.continued(snapshot)
                span.layer = self._layer
                span.component = self._component
                if self._tags:
                    for tag in self._tags:
                        span.tag(tag)
                return self._func(*args, **kwargs)

        return _continued_wrapper


def runnable(
        op: str = None,
        layer: Layer = Layer.Unknown,
        component: Component = Component.Unknown,
        tags: List[Tag] = None,
):
    def decorator(func):
        _op = op or f'Thread/{func.__name__}'
        return _RunnableWrapper(func, _op, layer, component, tags)

    return decorator
