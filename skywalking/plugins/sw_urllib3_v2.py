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

link_vector = ['https://urllib3.readthedocs.io/en/latest/']
support_matrix = {
    'urllib3': {
        '>=3.12': ['2.3', '2.0'],
    }
}
note = """urllib3 2.x plugin. For urllib3 1.x, see sw_urllib3."""


def install():
    from urllib3 import PoolManager

    # urllib3 2.x removed RequestMethods base class;
    # PoolManager.request is the direct entry point.
    # Guard: if RequestMethods still exists, this is urllib3 1.x — let sw_urllib3 handle it.
    try:
        from urllib3.request import RequestMethods  # noqa: F401
        return  # urllib3 1.x detected, skip — sw_urllib3 handles it
    except ImportError:
        pass  # urllib3 2.x, proceed

    _request = PoolManager.request

    def _sw_request(this: PoolManager, method, url, body=None, fields=None, headers=None, json=None, **urlopen_kw):
        from skywalking.utils.filter import sw_urlparse

        url_param = sw_urlparse(url)

        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(method) \
            else get_context().new_exit_span(op=url_param.path or '/', peer=url_param.netloc,
                                             component=Component.Urllib3)

        with span:
            carrier = span.inject()
            span.layer = Layer.Http

            if headers is None:
                headers = {}
            else:
                headers = dict(headers)
            for item in carrier:
                headers[item.key] = item.val

            span.tag(TagHttpMethod(method.upper()))
            span.tag(TagHttpURL(url_param.geturl()))

            res = _request(this, method, url, body=body, fields=fields, headers=headers, json=json, **urlopen_kw)

            span.tag(TagHttpStatusCode(res.status))
            if res.status >= 400:
                span.error_occurred = True

            return res

    PoolManager.request = _sw_request
