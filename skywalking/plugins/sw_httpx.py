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
from skywalking.trace.context import get_context, NoopContext
from skywalking.trace.span import NoopSpan
from skywalking.trace.tags import TagHttpMethod, TagHttpURL, TagHttpStatusCode

link_vector = ['https://www.python-httpx.org/']
support_matrix = {
    'httpx': {
        '>=3.7': ['0.23.*', '0.22.*']
    }
}
note = """"""


def install():
    from httpx import _client
    from httpx import USE_CLIENT_DEFAULT

    _async_send = _client.AsyncClient.send
    _send = _client.Client.send

    async def _sw_async_send(self, request, *, stream=False, auth=USE_CLIENT_DEFAULT,
                             follow_redirects=USE_CLIENT_DEFAULT, ):
        url_object = request.url

        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(
            request.method) else get_context().new_exit_span(op=url_object.path or '/', peer=url_object.netloc.decode(),
                                                             component=Component.HTTPX)
        with span:
            carrier = span.inject()
            span.layer = Layer.Http

            if not request.headers:
                request.headers = {}
            for item in carrier:
                request.headers[item.key] = item.val

            span.tag(TagHttpMethod(request.method.upper()))
            url_safe = str(url_object).replace(url_object.username, '').replace(url_object.password, '')

            span.tag(TagHttpURL(url_safe))

            res = await _async_send(self, request, stream=stream, auth=auth, follow_redirects=follow_redirects)

            status_code = res.status_code
            span.tag(TagHttpStatusCode(status_code))

            if status_code >= 400:
                span.error_occurred = True

            return res

    _client.AsyncClient.send = _sw_async_send

    def _sw_send(self, request, *, stream=False, auth=USE_CLIENT_DEFAULT, follow_redirects=USE_CLIENT_DEFAULT, ):
        url_object = request.url

        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(
            request.method) else get_context().new_exit_span(op=url_object.path or '/', peer=url_object.netloc.decode(),
                                                             component=Component.HTTPX)
        with span:
            carrier = span.inject()
            span.layer = Layer.Http

            if not request.headers:
                request.headers = {}
            for item in carrier:
                request.headers[item.key] = item.val

            span.tag(TagHttpMethod(request.method.upper()))
            url_safe = str(url_object).replace(url_object.username, '').replace(url_object.password, '')

            span.tag(TagHttpURL(url_safe))

            res = _send(self, request, stream=stream, auth=auth, follow_redirects=follow_redirects)

            status_code = res.status_code
            span.tag(TagHttpStatusCode(status_code))

            if status_code >= 400:
                span.error_occurred = True

            return res

    _client.Client.send = _sw_send
