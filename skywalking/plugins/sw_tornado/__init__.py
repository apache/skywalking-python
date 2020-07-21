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
import logging
from inspect import iscoroutinefunction

from skywalking import Layer, Component
from skywalking.trace import tags
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag

logger = logging.getLogger(__name__)


def install():
    try:
        from tornado import version_info as TORNADO_VERSION
        from tornado.gen import coroutine
        from tornado.web import RequestHandler
        if TORNADO_VERSION < (5, 0):
            logger.warning('Tornado 5+ required')
            return
        old_execute = RequestHandler._execute
        old_log_exception = RequestHandler.log_exception

        awaitable = iscoroutinefunction(old_execute)
        if awaitable:
            async def _sw_get_response(self, *args, **kwargs):
                # type: (RequestHandler, *Any, **Any) -> Any
                request = self.request
                context = get_context()
                carrier = Carrier()
                for item in carrier:
                    if item.key.capitalize() in request.headers:
                        item.val = request.headers[item.key.capitalize()]
                with context.new_entry_span(op=request.path, carrier=carrier) as span:
                    span.layer = Layer.Http
                    span.component = Component.Tornado
                    span.peer = '{}:{}'.format(request.host, request.port)
                    span.tag(Tag(key=tags.HttpMethod, val=request.method))
                    span.tag(
                        Tag(key=tags.HttpUrl, val='{}://{}{}'.format(request.protocol, request.host, request.path)))
                    resp = await old_execute(self, *args, **kwargs)
                    span.tag(Tag(key=tags.HttpStatus, val=resp.status_code))
                    if resp.status_code >= 400:
                        span.error_occurred = True
                return resp
        else:
            @coroutine
            def _sw_get_response(self, *args, **kwargs):
                # type: (RequestHandler, *Any, **Any) -> Any
                request = self.request
                context = get_context()
                carrier = Carrier()
                for item in carrier:
                    if item.key.capitalize() in request.headers:
                        item.val = request.headers[item.key.capitalize()]
                with context.new_entry_span(op=request.path, carrier=carrier) as span:
                    span.layer = Layer.Http
                    span.component = Component.Tornado
                    span.peer = '{}:{}'.format(request.host, request.port)
                    span.tag(Tag(key=tags.HttpMethod, val=request.method))
                    span.tag(
                        Tag(key=tags.HttpUrl, val='{}://{}{}'.format(request.protocol, request.host, request.path)))
                    resp = yield from old_execute(self, *args, **kwargs)
                    span.tag(Tag(key=tags.HttpStatus, val=resp.status_code))
                    if resp.status_code >= 400:
                        span.error_occurred = True
                return resp

        RequestHandler._execute = _sw_get_response  # type: ignore

        def _sw_handler_uncaught_exception(self, ty, value, tb, *args, **kwargs):
            # type: (Any, type, BaseException, Any, *Any, **Any) -> Optional[Any]
            if value is not None:
                entry_span = get_context().active_span()
                if entry_span is not None:
                    entry_span.raised()

            return old_log_exception(self, ty, value, tb, *args, **kwargs)  # type: ignore

        RequestHandler.log_exception = _sw_handler_uncaught_exception  # type: ignore
    except Exception:
        logger.warning('failed to install plugin %s', __name__)
