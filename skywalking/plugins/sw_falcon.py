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
from skywalking.trace.tags import TagHttpMethod, TagHttpURL, TagHttpParams, TagHttpStatusCode, TagHttpStatusMsg

link_vector = ['https://falcon.readthedocs.io/en/stable/']
support_matrix = {
    'hug': {
        '>=3.10': ['2.5', '2.6'],  # api deprecated for 3.10
        '>=3.6': ['2.4.1', '2.5', '2.6'],  # support begins 2.4.1
    }
}
note = """"""


def install():
    from falcon import API, request, RequestOptions

    _original_falcon_api = API.__call__

    def _sw_falcon_api(this: API, env, start_response):
        context = get_context()
        carrier = Carrier()
        req = request.Request(env, RequestOptions())
        headers = req.headers
        method = req.method

        for item in carrier:
            key = item.key.upper()
            if key in headers:
                item.val = headers[key]

        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(method) \
            else context.new_entry_span(op=req.path, carrier=carrier)

        with span:
            span.layer = Layer.Http
            span.component = Component.Falcon
            span.peer = req.remote_addr

            span.tag(TagHttpMethod(method))
            span.tag(TagHttpURL(str(req.url)))

            if req.params:
                span.tag(TagHttpParams(','.join([f'{k}={v}' for k, v in req.params.items()])))

            def _start_response(resp_status, headers):
                try:
                    code, msg = resp_status.split(' ', 1)
                    code = int(code)
                except Exception:
                    code, msg = 500, 'Internal Server Error'

                if code >= 400:
                    span.error_occurred = True

                span.tag(TagHttpStatusCode(code))
                span.tag(TagHttpStatusMsg(msg))

                return start_response(resp_status, headers)

            try:
                return _original_falcon_api(this, env, _start_response)

            except Exception:
                span.raised()

                raise

    API.__call__ = _sw_falcon_api
