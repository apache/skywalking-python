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
    'falcon': {
        '>=3.13': ['4.*'],
        '>=3.10': ['3.1.*', '4.*'],
    }
}
note = """Falcon 3.x/4.x plugin. For legacy hug-based instrumentation, see sw_falcon."""


def install():
    from falcon import App

    # Guard: if falcon.App doesn't exist, this is falcon 2.x or older — let sw_falcon handle it
    _original_falcon_app = App.__call__

    def _sw_falcon_app(this: App, env, start_response):
        from falcon import Request, RequestOptions

        context = get_context()
        carrier = Carrier()
        req = Request(env, RequestOptions())
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
                return _original_falcon_app(this, env, _start_response)

            except Exception:
                span.raised()

                raise

    App.__call__ = _sw_falcon_app
