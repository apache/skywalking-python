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
from asyncio import coroutine
from inspect import iscoroutinefunction, isawaitable

from starlette.types import ASGIApp, Receive, Scope, Send, Message
from skywalking import Layer, Component, config
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context, NoopContext
from skywalking.trace.span import NoopSpan
from skywalking.trace.tags import TagHttpMethod, TagHttpURL, TagHttpStatusCode, TagHttpParams

link_vector = ['https://flask.palletsprojects.com']
support_matrix = {
    'fastapi': {
        '>=3.6': ['1.1', '2.0']  # 1.1 to be removed in near future
    }
}
note = """"""


def install():
    from fastapi import routing
    from fastapi.routing import APIRoute

    from starlette.responses import Response

    old_execute = APIRoute.handle
    APIRoute.handle = _gen_sw_get_response_func(old_execute)

def _gen_sw_get_response_func(old_execute):
    from fastapi import routing
    print(123)
    is_coroutine = routing.iscoroutinefunction_or_partial(old_execute)
    if is_coroutine:
        async def _sw_get_response(self, scope: Scope, receive: Receive, send: Send):
            from starlette.requests import Request
            req = Request(scope, receive=receive, send=send)
            result = old_execute(self, scope, receive, send)
            print(result)
            if isawaitable(result):
                result = await result
                print(result)
            return result
    else:
        @coroutine
        def _sw_get_response(self, scope: Scope, receive: Receive, send: Send):
            result = yield from old_execute(self, scope, receive, send)
            print(result)
            return result
    return _sw_get_response


