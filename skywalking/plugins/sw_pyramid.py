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
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag


def install():
    from pyramid.router import Router

    def _sw_invoke_request(self, request, *args, **kwargs):
        context = get_context()
        carrier = Carrier()

        for item in carrier:
            val = request.headers.get(item.key)

            if val is not None:
                item.val = val

        with context.new_entry_span(op=request.path, carrier=carrier) as span:
            span.layer = Layer.Http
            span.component = Component.Pyramid
            span.peer = request.remote_host or request.remote_addr

            span.tag(Tag(key=tags.HttpMethod, val=request.method))
            span.tag(Tag(key=tags.HttpUrl, val=str(request.url)))

            resp = _invoke_request(self, request, *args, **kwargs)

            span.tag(Tag(key=tags.HttpStatus, val=resp.status_code, overridable=True))

            if resp.status_code >= 400:
                span.error_occurred = True

        return resp

    _invoke_request = Router.invoke_request
    Router.invoke_request = _sw_invoke_request
