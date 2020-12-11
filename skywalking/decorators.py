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

from functools import wraps
from typing import List
import inspect

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
        context = get_context()

        span = context.new_local_span(op=_op)
        span.layer = layer
        span.component = component
        [span.tag(tag) for tag in tags or []]

        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                with span:
                    return await func(*args, **kwargs)
            return wrapper

        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                with span:
                    return func(*args, **kwargs)
            return wrapper

    return decorator


def runnable(
        op: str = None,
        layer: Layer = Layer.Unknown,
        component: Component = Component.Unknown,
        tags: List[Tag] = None,
):
    def decorator(func):
        snapshot = get_context().capture()

        @wraps(func)
        def wrapper(*args, **kwargs):
            _op = op or "Thread/"+func.__name__
            context = get_context()
            with context.new_local_span(op=_op) as span:
                context.continued(snapshot)
                span.layer = layer
                span.component = component
                [span.tag(tag) for tag in tags or []]
                func(*args, **kwargs)

        return wrapper

    return decorator
