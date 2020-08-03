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

from skywalking import Layer, Component
from skywalking.trace.context import get_context


def trace(
        op: str = None,
        layer: Layer = Layer.Unknown,
        component: Component = Component.Unknown,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _op = op or func.__name__
            context = get_context()
            with context.new_local_span(op=_op) as span:
                span.layer = layer
                span.component = component
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception:
                    span.raised()
                    raise

        return wrapper

    return decorator
