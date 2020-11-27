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

from skywalking import Layer, Component, config
from skywalking.trace import tags
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.span import NoopSpan
from skywalking.trace.tags import Tag

logger = logging.getLogger(__name__)

version_rule = {
    "name": "sanic",
    "rules": [">=20.3.0"]
}


def install():
    from sanic import Sanic, handlers, response

    _format_http1_response = response.format_http1_response
    _handle_request = Sanic.handle_request
    _handlers_ErrorHandler_reponse = handlers.ErrorHandler.response

    def _sw_format_http1_reponse(status: int, headers, body=b""):
        if status is not None:
            entry_span = get_context().active_span()
            if entry_span is not None and type(entry_span) is not NoopSpan:
                if status >= 400:
                    entry_span.error_occurred = True
                entry_span.tag(Tag(key=tags.HttpStatus, val=status))

        return _format_http1_response(status, headers, body)

    def _sw_handlers_ErrorHandler_reponse(self: handlers.ErrorHandler, req, e):
        if e is not None:
            entry_span = get_context().active_span()
            if entry_span is not None and type(entry_span) is not NoopSpan:
                entry_span.raised()

        return _handlers_ErrorHandler_reponse(self, req, e)

    response.format_http1_response = _sw_format_http1_reponse
    Sanic.handle_request = _gen_sw_handle_request(_handle_request)
    handlers.ErrorHandler.response = _sw_handlers_ErrorHandler_reponse


def _gen_sw_handle_request(_handle_request):
    from inspect import isawaitable

    def params_tostring(params):
        return "\n".join([k + '=[' + ",".join(params.getlist(k)) + ']' for k, _ in params.items()])

    async def _sw_handle_request(self, request, write_callback, stream_callback):
        req = request
        context = get_context()
        carrier = Carrier()

        for item in carrier:
            if item.key.capitalize() in req.headers:
                item.val = req.headers[item.key.capitalize()]
        with context.new_entry_span(op=req.path, carrier=carrier) as span:
            span.layer = Layer.Http
            span.component = Component.Sanic
            span.peer = '%s:%s' % (req.remote_addr or req.ip, req.port)
            span.tag(Tag(key=tags.HttpMethod, val=req.method))
            span.tag(Tag(key=tags.HttpUrl, val=req.url.split("?")[0]))
            if config.sanic_collect_http_params and req.args:
                span.tag(Tag(key=tags.HttpParams,
                             val=params_tostring(req.args)[0:config.http_params_length_threshold]))
            resp = _handle_request(self, request, write_callback, stream_callback)
            if isawaitable(resp):
                result = await resp

        return result
    return _sw_handle_request
