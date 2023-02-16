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
from skywalking.trace.tags import TagHttpMethod, TagHttpParams, TagHttpStatusCode, TagHttpURL

link_vector = ['http://bottlepy.org/docs/dev/']
support_matrix = {
    'bottle': {
        '>=3.7': ['0.12.23']
    }
}
note = """"""


def install():
    from bottle import Bottle
    from wsgiref.simple_server import WSGIRequestHandler

    _app_call = Bottle.__call__
    _get_environ = WSGIRequestHandler.get_environ

    def params_tostring(params):
        return '\n'.join([f"{k}=[{','.join(params.getlist(k))}]" for k, _ in params.items()])

    def sw_get_environ(self):
        env = _get_environ(self)
        env['REMOTE_PORT'] = self.client_address[1]
        return env

    def sw_app_call(self, environ, start_response):
        from bottle import response
        from bottle import LocalRequest

        request = LocalRequest()
        request.bind(environ)
        carrier = Carrier()
        method = request.method

        for item in carrier:
            if item.key.capitalize() in request.headers:
                item.val = request.headers[item.key.capitalize()]

        span = NoopSpan(NoopContext()) if config.ignore_http_method_check(method) \
            else get_context().new_entry_span(op=request.path, carrier=carrier, inherit=Component.General)

        with span:
            span.layer = Layer.Http
            span.component = Component.Bottle
            if all(environ_key in environ for environ_key in ('REMOTE_ADDR', 'REMOTE_PORT')):
                span.peer = f"{environ['REMOTE_ADDR']}:{environ['REMOTE_PORT']}"
            span.tag(TagHttpMethod(method))
            span.tag(TagHttpURL(request.url.split('?')[0]))

            if config.plugin_bottle_collect_http_params and request.query:
                span.tag(TagHttpParams(params_tostring(request.query)[0:config.plugin_http_http_params_length_threshold]))

            res = _app_call(self, environ, start_response)

            span.tag(TagHttpStatusCode(response.status_code))
            if response.status_code >= 400:
                span.error_occurred = True

            return res

    Bottle.__call__ = sw_app_call
    WSGIRequestHandler.get_environ = sw_get_environ
