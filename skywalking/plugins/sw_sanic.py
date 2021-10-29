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
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context, NoopContext
from skywalking.trace.span import NoopSpan
from skywalking.trace.tags import TagHttpMethod, TagHttpURL, TagHttpStatusCode, TagHttpParams

logger = logging.getLogger(__name__)

# version_rule = {
#     "name": "sanic",
#     "rules": [">=20.3.0 <21.0.0"]
# }

link_vector = ['https://sanic.readthedocs.io/en/latest']
support_matrix = {
    'sanic': {
        '>=3.10': [],  # not supporting any version yet
        '>=3.7': ['20.12'],  # 21.9 Future LTS - Not supported by SW yet
        '>=3.6': ['20.12']  # 20.12 last LTS for python 3.6
    }  # TODO: add instrumentation for 21.9 (method signature change) remove - write_callback, stream_callback
}
note = """"""


def install():
    from sanic import Sanic, handlers, response
    # TODO: format_http1_response is removed from response in later versions.

    _format_http1_response = response.format_http1_response
    _handle_request = Sanic.handle_request
    _handlers_ErrorHandler_response = handlers.ErrorHandler.response # noqa

    def _sw_format_http1_response(status: int, headers, body=b''):
        if status is not None:
            entry_span = get_context().active_span()
            if entry_span is not None and type(entry_span) is not NoopSpan:
                if status >= 400:
                    entry_span.error_occurred = True
                entry_span.tag(TagHttpStatusCode(status))

        return _format_http1_response(status, headers, body)

    def _sw_handlers_ErrorHandler_response(self: handlers.ErrorHandler, req, e): # noqa
        if e is not None:
            entry_span = get_context().active_span()
            if entry_span is not None and type(entry_span) is not NoopSpan:
                entry_span.raised()

        return _handlers_ErrorHandler_response(self, req, e)

    response.format_http1_response = _sw_format_http1_response
    Sanic.handle_request = _gen_sw_handle_request(_handle_request)
    handlers.ErrorHandler.response = _sw_handlers_ErrorHandler_response


def _gen_sw_handle_request(_handle_request):
    from inspect import isawaitable

    def params_tostring(params):
        return '\n'.join([f"{k}=[{','.join(params.getlist(k))}]" for k, _ in params.items()])

    async def _sw_handle_request(self, request, write_callback, stream_callback):
        req = request
        carrier = Carrier()
        method = req.method

        for item in carrier:
            if item.key.capitalize() in req.headers:
                item.val = req.headers[item.key.capitalize()]

        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(method) \
            else get_context().new_entry_span(op=req.path, carrier=carrier)

        with span:
            span.layer = Layer.Http
            span.component = Component.Sanic
            span.peer = f'{req.remote_addr or req.ip}:{req.port}'
            span.tag(TagHttpMethod(method))
            span.tag(TagHttpURL(req.url.split('?')[0]))
            if config.sanic_collect_http_params and req.args:
                span.tag(TagHttpParams(params_tostring(req.args)[0:config.http_params_length_threshold]))
            resp = _handle_request(self, request, write_callback, stream_callback)
            if isawaitable(resp):
                result = await resp

        return result

    return _sw_handle_request
