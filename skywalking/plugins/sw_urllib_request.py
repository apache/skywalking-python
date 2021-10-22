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

from urllib.request import Request

from skywalking import Layer, Component, config
from skywalking.trace.context import get_context, NoopContext
from skywalking.trace.span import NoopSpan
from skywalking.trace.tags import TagHttpMethod, TagHttpURL, TagHttpStatusCode

link_vector = ['https://docs.python.org/3/library/urllib.request.html']
support_matrix = {
    'urllib_request': {
        '>=3.6': ['*']
    }
}
note = """"""


def install():
    import socket
    from urllib.request import OpenerDirector
    from urllib.error import HTTPError

    _open = OpenerDirector.open

    def _sw_open(this: OpenerDirector, fullurl, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        if isinstance(fullurl, str):
            fullurl = Request(fullurl, data)

        url = fullurl.selector.split('?')[0] if fullurl.selector else '/'
        method = getattr(fullurl, 'method', None) or ('GET' if data is None else 'POST')

        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(method) \
            else get_context().new_exit_span(op=url, peer=fullurl.host, component=Component.General)

        with span:
            carrier = span.inject()
            span.layer = Layer.Http
            code = None

            for item in carrier:
                fullurl.add_header(item.key, item.val)

            try:
                res = _open(this, fullurl, data, timeout)
                code = res.code
            except HTTPError as e:
                code = e.code
                raise
            finally:  # we do this here because it may change in _open()
                span.tag(TagHttpMethod(method))
                span.tag(TagHttpURL(fullurl.full_url))

                if code is not None:
                    span.tag(TagHttpStatusCode(code))

                    if code >= 400:
                        span.error_occurred = True

            return res

    OpenerDirector.open = _sw_open
