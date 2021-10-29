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

from skywalking import Layer, Component, config
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context, NoopContext
from skywalking.trace.span import NoopSpan
from skywalking.trace.tags import TagHttpMethod, TagHttpURL, TagHttpStatusCode

link_vector = ['https://docs.aiohttp.org']
support_matrix = {
    'aiohttp': {
        '>=3.10': [],  # waiting for 3.8 release
        '>=3.6': ['3.7.4']
    }
}
note = """"""


def install():
    from aiohttp import ClientSession
    from aiohttp.web_protocol import RequestHandler
    from multidict import CIMultiDict, MultiDict, MultiDictProxy
    from yarl import URL

    async def _sw_request(self: ClientSession, method: str, str_or_url, **kwargs):
        url = URL(str_or_url).with_user(None).with_password(None)
        peer = f"{url.host or ''}:{url.port or ''}"

        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(method) \
            else get_context().new_exit_span(op=url.path or '/', peer=peer, component=Component.AioHttp)

        with span:
            span.layer = Layer.Http
            span.tag(TagHttpMethod(method.upper()))  # pyre-ignore
            span.tag(TagHttpURL(str(url.with_password(None))))  # pyre-ignore

            carrier = span.inject()
            headers = kwargs.get('headers')

            if headers is None:
                headers = kwargs['headers'] = CIMultiDict()
            elif not isinstance(headers, (MultiDictProxy, MultiDict)):
                headers = CIMultiDict(headers)

            for item in carrier:
                headers.add(item.key, item.val)

            res = await _request(self, method, str_or_url, **kwargs)

            span.tag(TagHttpStatusCode(res.status))

            if res.status >= 400:
                span.error_occurred = True

            return res

    _request = ClientSession._request
    ClientSession._request = _sw_request

    async def _sw_handle_request(self, request, start_time: float):
        carrier = Carrier()
        method = request.method

        for item in carrier:
            val = request.headers.get(item.key)

            if val is not None:
                item.val = val

        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(method) \
            else get_context().new_entry_span(op=request.path, carrier=carrier)

        with span:
            span.layer = Layer.Http
            span.component = Component.AioHttp
            peer_name = request._transport_peername
            if isinstance(peer_name, (list, tuple)):
                span.peer = f'{peer_name[0]}:{peer_name[1]}'
            else:
                span.peer = f'{peer_name}'

            span.tag(TagHttpMethod(method))  # pyre-ignore
            span.tag(TagHttpURL(str(request.url)))  # pyre-ignore

            resp, reset = await _handle_request(self, request, start_time)

            span.tag(TagHttpStatusCode(resp.status))

            if resp.status >= 400:
                span.error_occurred = True

        return resp, reset

    _handle_request = RequestHandler._handle_request
    RequestHandler._handle_request = _sw_handle_request
