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
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag


def install():
    from aiohttp import ClientSession
    from multidict import CIMultiDict, MultiDict, MultiDictProxy
    from yarl import URL

    async def _sw_request(self: ClientSession, method: str, str_or_url, **kwargs):
        url = URL(str_or_url)
        peer = \
            (url.scheme + '://' if url.scheme else '') + \
            ((url.user or '') + ':' + (url.password or '') + '@' if url.user or url.password else '') + \
            (url.host or '') + \
            (':' + str(url.explicit_port) if url.explicit_port is not None else '')
        context = get_context()

        with context.new_exit_span(op=url.path or "/", peer=peer) as span:
            span.layer = Layer.Http
            span.component = Component.Unknown  # TODO: add Component.aiohttp
            span.tag(Tag(key=tags.HttpMethod, val=method.upper()))  # pyre-ignore
            span.tag(Tag(key=tags.HttpUrl, val=url))  # pyre-ignore

            carrier = span.inject()
            headers = kwargs.get('headers')

            if headers is None:
                headers = CIMultiDict()
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
