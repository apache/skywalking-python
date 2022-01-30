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

from starlette.types import ASGIApp, Receive, Scope, Send
from skywalking import Layer, Component, config
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context, NoopContext
from skywalking.trace.span import NoopSpan
from skywalking.trace.tags import TagHttpMethod, TagHttpURL, TagHttpStatusCode, TagHttpParams

link_vector = ['https://flask.palletsprojects.com']
support_matrix = {
    'flask': {
        '>=3.6': ['1.1', '2.0']  # 1.1 to be removed in near future
    }
}
note = """"""


def install():
    from fastapi import routing
    from fastapi.routing import APIRoute

    _handle = APIRoute.handle

    def params_tostring(params):
        return '\n'.join([f"{k}=[{','.join(params.getlist(k))}]" for k, _ in params.items()])

    async def _sw_handle(self, scope: Scope, receive: Receive, send: Send):
        from starlette.requests import Request
        req = Request(scope, receive=receive, send=send)
        carrier = Carrier()
        method = req.method

        for item in carrier:
            if item.key.capitalize() in req.headers:
                item.val = req.headers[item.key.capitalize()]

        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(method) \
            else get_context().new_entry_span(op=dict(scope)["path"], carrier=carrier, inherit=Component.General)

        with span:
            span.layer = Layer.Http
            span.component = Component.Flask
            span.peer = f"{req.client.host}:{req.client.port}"
            span.tag(TagHttpMethod(method))
            span.tag(TagHttpURL(req.url._url.split('?')[0]))
            if config.fastapi_collect_http_params and req.values:
                span.tag(TagHttpParams(params_tostring(req.values)[0:config.http_params_length_threshold]))
            res = await _handle(self, scope, receive, send)
            # if isawaitable(resp):
            #     result = await resp
            # if resp.status_code >= 400:
            #     span.error_occurred = True

            # span.tag(TagHttpStatusCode(resp.status_code))
        return res

    APIRoute.handle = _sw_handle
