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
from skywalking.trace import tags
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag

version_rule = {
    "name": "django",
    "rules": [">=2.0"]
}


def install():
    from django.core.handlers.base import BaseHandler
    from django.core.handlers import exception

    _get_response = BaseHandler.get_response
    _handle_uncaught_exception = exception.handle_uncaught_exception

    def _sw_get_response(this, request):
        if request is None:
            resp = _get_response(this, request)
            return resp

        context = get_context()
        carrier = Carrier()
        for item in carrier:
            # Any HTTP headers in the request are converted to META keys by converting all characters to uppercase,
            # replacing any hyphens with underscores and adding an HTTP_ prefix to the name.
            # https://docs.djangoproject.com/en/3.0/ref/request-response/#django.http.HttpRequest.META
            sw_http_header_key = 'HTTP_%s' % item.key.upper().replace('-', '_')
            if sw_http_header_key in request.META:
                item.val = request.META[sw_http_header_key]

        with context.new_entry_span(op=request.path, carrier=carrier) as span:
            span.layer = Layer.Http
            span.component = Component.Django
            span.peer = '%s:%s' % (request.META.get('REMOTE_ADDR'), request.META.get('REMOTE_PORT') or "80")

            span.tag(Tag(key=tags.HttpMethod, val=request.method))
            span.tag(Tag(key=tags.HttpUrl, val=request.build_absolute_uri().split("?")[0]))

            # you can get request parameters by `request.GET` even though client are using POST or other methods
            if config.django_collect_http_params and request.GET:
                span.tag(Tag(key=tags.HttpParams,
                             val=params_tostring(request.GET)[0:config.http_params_length_threshold]))

            resp = _get_response(this, request)
            span.tag(Tag(key=tags.HttpStatus, val=resp.status_code, overridable=True))
            if resp.status_code >= 400:
                span.error_occurred = True
            return resp

    def _sw_handle_uncaught_exception(request, resolver, exc_info):
        if exc_info is not None:
            entry_span = get_context().active_span()
            if entry_span is not None:
                entry_span.raised()

        return _handle_uncaught_exception(request, resolver, exc_info)

    BaseHandler.get_response = _sw_get_response
    exception.handle_uncaught_exception = _sw_handle_uncaught_exception


def params_tostring(params):
    return "\n".join([k + '=[' + ",".join(params.getlist(k)) + ']' for k, _ in params.items()])
