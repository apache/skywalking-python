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

from skywalking import Layer, Component
from skywalking.trace import tags
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag


def install():
    from aiohttp import ClientSession
    from aiohttp.web_protocol import RequestHandler
    from multidict import CIMultiDict, MultiDict, MultiDictProxy
    from yarl import URL

    async def _sw_request(self: ClientSession, method: str, str_or_url, **kwargs):
        url = URL(str_or_url).with_user(None).with_password(None)
        peer = '%s:%d' % (url.host or '', url.port)
        context = get_context()

        with context.new_exit_span(op=url.path or "/", peer=peer) as span:
            span.layer = Layer.Http
            span.component = Component.AioHttp
            span.tag(Tag(key=tags.HttpMethod, val=method.upper()))  # pyre-ignore
            span.tag(Tag(key=tags.HttpUrl, val=url))  # pyre-ignore

            carrier = span.inject()
            headers = kwargs.get('headers')

            if headers is None:
                headers = kwargs['headers'] = CIMultiDict()
            elif not isinstance(headers, (MultiDictProxy, MultiDict)):
                headers = CIMultiDict(headers)

            for item in carrier:
                headers.add(item.key, item.val)

            res = await _request(self, method, str_or_url, **kwargs)

            span.tag(Tag(key=tags.HttpStatus, val=res.status, overridable=True))

            if res.status >= 400:
                span.error_occurred = True

            return res

    _request = ClientSession._request
    ClientSession._request = _sw_request

    async def _sw_handle_request(self, request, start_time: float):
        context = get_context()
        carrier = Carrier()

        for item in carrier:
            val = request.headers.get(item.key)

            if val is not None:
                item.val = val

        with context.new_entry_span(op=request.path, carrier=carrier) as span:
            span.layer = Layer.Http
            span.component = Component.AioHttp
            span.peer = '%s:%d' % request._transport_peername if isinstance(request._transport_peername, (list, tuple))\
                else request._transport_peername

            span.tag(Tag(key=tags.HttpMethod, val=request.method))  # pyre-ignore
            span.tag(Tag(key=tags.HttpUrl, val=str(request.url)))  # pyre-ignore

            resp, reset = await _handle_request(self, request, start_time)

            span.tag(Tag(key=tags.HttpStatus, val=resp.status, overridable=True))

            if resp.status >= 400:
                span.error_occurred = True

        return resp, reset

    _handle_request = RequestHandler._handle_request
    RequestHandler._handle_request = _sw_handle_request
