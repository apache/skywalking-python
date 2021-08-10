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
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.span import NoopSpan
from skywalking.trace.tags import TagHttpMethod, TagHttpURL, TagHttpParams, TagHttpStatusCode


def install():
    from falcon import API, request, response

    _original_falcon_api = API.__call__
    _original_falcon_handle_exception = API._handle_exception

    def params_tostring(params):
        return "\n".join([k + "=" + v for k, v in params.items()])

    def _sw_falcon_api(this: API, env, start_response):
        context = get_context()
        carrier = Carrier()
        headers = get_headers(env)
        for item in carrier:
            key = item.key.replace("_", "-") if "_" in item.key else item.key
            if key.capitalize() in headers:
                item.val = headers[key.capitalize()]
        with context.new_entry_span(op="/", carrier=carrier) as span:
            span.layer = Layer.Http
            span.component = Component.Falcon

            from falcon import RequestOptions

            req = request.Request(env, RequestOptions())
            span.op = str(req.url).split("?")[0]
            span.peer = "%s:%s" % (req.remote_addr, req.port)

            span.tag(TagHttpMethod(req.method))
            span.tag(TagHttpURL(str(req.url)))
            if req.params:
                span.tag(TagHttpParams(params_tostring(req.params)[0:]))

            resp = _original_falcon_api(this, env, start_response)

            from falcon import ResponseOptions

            resp_obj = response.Response(ResponseOptions())

            resp_status = parse_status(resp_obj.status)
            if int(resp_status[0]) >= 400:
                span.error_occurred = True

            span.tag(TagHttpStatusCode(int(resp_status[0])))

            return resp

    def _sw_handle_exception(this: API, req, resp, ex, params):
        if ex is not None:
            entry_span = get_context().active_span()
            if entry_span is not None and type(entry_span) is not NoopSpan:
                entry_span.raised()

        return _original_falcon_handle_exception(this, req, resp, ex, params)

    API.__call__ = _sw_falcon_api
    API._handle_exception = _sw_handle_exception


def get_headers(env):
    headers = {}
    wsgi_content_headers = frozenset(["CONTENT_TYPE", "CONTENT_LENGTH"])

    for name, value in env.items():
        if name.startswith("HTTP_"):
            headers[name[5:].replace("_", "-")] = value

        elif name in wsgi_content_headers:
            headers[name.replace("_", "-")] = value

    return headers


def parse_status(status_str):
    return status_str.split(" ") if status_str else [404, "status is empty"]
