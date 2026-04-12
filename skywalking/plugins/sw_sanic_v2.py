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

link_vector = ['https://sanic.readthedocs.io/en/latest']
support_matrix = {
    'sanic': {
        '>=3.10': ['23.12.2', '24.12.0'],
    }
}
note = """Sanic 21.9+ plugin using signal listeners.
For legacy Sanic <=21.3, see sw_sanic.
Note: Sanic's touchup system recompiles handle_request at startup,
so we use signal listeners instead of monkey-patching handle_request."""


def install():
    from sanic import Sanic

    # Guard: if handle_request still has write_callback param, this is old Sanic — let sw_sanic handle it
    import inspect
    sig = inspect.signature(Sanic.handle_request)
    if 'write_callback' in sig.parameters:
        return  # old Sanic, skip

    _original_init = Sanic.__init__

    def _sw_init(self, *args, **kwargs):
        _original_init(self, *args, **kwargs)
        _register_listeners(self)

    Sanic.__init__ = _sw_init


def _register_listeners(app):

    def params_tostring(params):
        return '\n'.join([f"{k}=[{','.join(params.getlist(k))}]" for k, _ in params.items()])

    @app.on_request
    async def sw_on_request(request):
        carrier = Carrier()
        method = request.method

        for item in carrier:
            if item.key.capitalize() in request.headers:
                item.val = request.headers[item.key.capitalize()]

        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(method) \
            else get_context().new_entry_span(op=request.path, carrier=carrier)

        span.start()
        span.layer = Layer.Http
        span.component = Component.Sanic
        span.peer = f'{request.remote_addr or request.ip}:{request.port}'
        span.tag(TagHttpMethod(method))
        span.tag(TagHttpURL(request.url.split('?')[0]))
        if config.plugin_sanic_collect_http_params and request.args:
            span.tag(TagHttpParams(
                params_tostring(request.args)[0:config.plugin_http_http_params_length_threshold]
            ))

        request.ctx._sw_span = span

    @app.on_response
    async def sw_on_response(request, response):
        span = getattr(request.ctx, '_sw_span', None)
        if span is None:
            return

        if response is not None:
            span.tag(TagHttpStatusCode(response.status))
            if response.status >= 400:
                span.error_occurred = True

        span.stop()
