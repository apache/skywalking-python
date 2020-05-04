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

import inspect

from skywalking import Layer, Component
from skywalking.trace.context import get_context


def install():
    from http.server import BaseHTTPRequestHandler

    _handle = BaseHTTPRequestHandler.handle

    def _sw_handle(this: BaseHTTPRequestHandler):
        http_methods = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH')
        for method in http_methods:
            if hasattr(this, 'do_' + method) and inspect.ismethod(getattr(this, 'do_' + method)):
                _do_method = getattr(this, 'do_' + method)

                def _sw_do_method():
                    context = get_context()
                    with context.new_entry_span(op=this.path) as span:
                        span.layer = Layer.Http
                        span.component = Component.Http
                        span.peer = '%s:%s' % this.client_address
                        _do_method()

                setattr(this, 'do_' + method, _sw_do_method)
        _handle(this)

    BaseHTTPRequestHandler.handle = _sw_handle
