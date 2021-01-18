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

from inspect import iscoroutinefunction, isawaitable

from skywalking import Layer, Component
from skywalking.trace import tags
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag


def install():
    from tornado.web import RequestHandler
    old_execute = RequestHandler._execute
    old_log_exception = RequestHandler.log_exception
    RequestHandler._execute = _gen_sw_get_response_func(old_execute)

    def _sw_handler_uncaught_exception(self: RequestHandler, ty, value, tb, *args, **kwargs):
        if value is not None:
            entry_span = get_context().active_span()
            if entry_span is not None:
                entry_span.raised()

        return old_log_exception(self, ty, value, tb, *args, **kwargs)

    RequestHandler.log_exception = _sw_handler_uncaught_exception


def _gen_sw_get_response_func(old_execute):
    from tornado.gen import coroutine

    awaitable = iscoroutinefunction(old_execute)
    if awaitable:
        # Starting Tornado 6 RequestHandler._execute method is a standard Python coroutine (async/await)
        # In that case our method should be a coroutine function too
        async def _sw_get_response(self, *args, **kwargs):
            request = self.request
            context = get_context()
            carrier = Carrier()
            for item in carrier:
                if item.key.capitalize() in request.headers:
                    item.val = request.headers[item.key.capitalize()]
            with context.new_entry_span(op=request.path, carrier=carrier) as span:
                span.layer = Layer.Http
                span.component = Component.Tornado
                peer = request.connection.stream.socket.getpeername()
                span.peer = '{0}:{1}'.format(*peer)
                span.tag(Tag(key=tags.HttpMethod, val=request.method))
                span.tag(
                    Tag(key=tags.HttpUrl, val='{}://{}{}'.format(request.protocol, request.host, request.path)))
                result = old_execute(self, *args, **kwargs)
                if isawaitable(result):
                    result = await result
                span.tag(Tag(key=tags.HttpStatus, val=self._status_code, overridable=True))
                if self._status_code >= 400:
                    span.error_occurred = True
            return result
    else:
        @coroutine
        def _sw_get_response(self, *args, **kwargs):
            request = self.request
            context = get_context()
            carrier = Carrier()
            for item in carrier:
                if item.key.capitalize() in request.headers:
                    item.val = request.headers[item.key.capitalize()]
            with context.new_entry_span(op=request.path, carrier=carrier) as span:
                span.layer = Layer.Http
                span.component = Component.Tornado
                peer = request.connection.stream.socket.getpeername()
                span.peer = '{0}:{1}'.format(*peer)
                span.tag(Tag(key=tags.HttpMethod, val=request.method))
                span.tag(
                    Tag(key=tags.HttpUrl, val='{}://{}{}'.format(request.protocol, request.host, request.path)))
                result = yield from old_execute(self, *args, **kwargs)
                span.tag(Tag(key=tags.HttpStatus, val=self._status_code, overridable=True))
                if self._status_code >= 400:
                    span.error_occurred = True
            return result
    return _sw_get_response
