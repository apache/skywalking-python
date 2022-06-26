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
from bottle import Router

link_vector = ['http://bottlepy.org/docs/dev/']

def do(environ):
    carrier = Carrier()
    path = environ.get('PATH_INFO')
    query = environ.get('QUERY_STRING')
    if query and query != '':
        path = path + '?' + query

    method = environ['REQUEST_METHOD'].upper()

    span = NoopSpan(NoopContext()) if config.ignore_http_method_check(method) \
        else get_context().new_entry_span(op=path.split('?')[0], carrier=carrier)

    with span:
        url = f"http://{environ.get('HTTP_HOST')}{path}"
        span.layer = Layer.Http
        span.component = Component.General
        span.peer = f'{environ.get("REMOTE_ADDR")}:{environ.get("REMOTE_PORT")}'
        span.tag(TagHttpMethod(method))
        span.tag(TagHttpURL(url))

def install():
    _match = Router.match

    def sw_match(self, environ):
        method = environ['REQUEST_METHOD'].upper()
        path = environ['PATH_INFO'] or '/'
        
        do(environ)

        return _match(self, environ)

    Router.match = sw_match