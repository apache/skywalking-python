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
import logging

from skywalking import Layer, Component
from skywalking.trace import tags
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag

logger = logging.getLogger(__name__)


def install():
    from http.server import BaseHTTPRequestHandler

    _handle = BaseHTTPRequestHandler.handle

    def _sw_handle(handler: BaseHTTPRequestHandler):
        clazz = handler.__class__
        if 'werkzeug.serving.WSGIRequestHandler' == ".".join([clazz.__module__, clazz.__name__]):
            wrap_werkzeug_request_handler(handler)
        else:
            wrap_default_request_handler(handler)
        _handle(handler)

    BaseHTTPRequestHandler.handle = _sw_handle

    def _sw_send_response_only(self, code, *args, **kwargs):
        self._status_code = code

        return _send_response_only(self, code, *args, **kwargs)

    _send_response_only = BaseHTTPRequestHandler.send_response_only
    BaseHTTPRequestHandler.send_response_only = _sw_send_response_only


def wrap_werkzeug_request_handler(handler):
    """
    Wrap run_wsgi of werkzeug.serving.WSGIRequestHandler to add skywalking instrument code.
    """
    _run_wsgi = handler.run_wsgi

    def _wrap_run_wsgi():
        context = get_context()
        carrier = Carrier()
        for item in carrier:
            item.val = handler.headers[item.key.capitalize()]
        path = handler.path or '/'
        with context.new_entry_span(op=path.split("?")[0], carrier=carrier) as span:
            url = 'http://' + handler.headers["Host"] + path if 'Host' in handler.headers else path
            span.layer = Layer.Http
            span.component = Component.General
            span.peer = '%s:%s' % handler.client_address
            span.tag(Tag(key=tags.HttpMethod, val=handler.command))
            span.tag(Tag(key=tags.HttpUrl, val=url))

            try:
                return _run_wsgi()
            finally:
                status_code = int(getattr(handler, '_status_code', -1))
                if status_code > -1:
                    span.tag(Tag(key=tags.HttpStatus, val=status_code))
                    if status_code >= 400:
                        span.error_occurred = True

    handler.run_wsgi = _wrap_run_wsgi

    def _sw_send_response(self, code, *args, **kwargs):
        self._status_code = code

        return _send_response(self, code, *args, **kwargs)

    WSGIRequestHandler = handler.__class__

    if not getattr(WSGIRequestHandler, '_sw_wrapped', False):
        _send_response = WSGIRequestHandler.send_response
        WSGIRequestHandler.send_response = _sw_send_response
        WSGIRequestHandler._sw_wrapped = True


def wrap_default_request_handler(handler):
    http_methods = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH')
    for method in http_methods:
        _wrap_do_method(handler, method)


def _wrap_do_method(handler, method):
    if hasattr(handler, 'do_' + method) and inspect.ismethod(getattr(handler, 'do_' + method)):
        _do_method = getattr(handler, 'do_' + method)

        def _sw_do_method():
            context = get_context()
            carrier = Carrier()
            for item in carrier:
                item.val = handler.headers[item.key.capitalize()]
            path = handler.path or '/'
            with context.new_entry_span(op=path.split("?")[0], carrier=carrier) as span:
                url = 'http://' + handler.headers["Host"] + path if 'Host' in handler.headers else path
                span.layer = Layer.Http
                span.component = Component.General
                span.peer = '%s:%s' % handler.client_address
                span.tag(Tag(key=tags.HttpMethod, val=method))
                span.tag(Tag(key=tags.HttpUrl, val=url))

                try:
                    _do_method()
                finally:
                    status_code = int(getattr(handler, '_status_code', -1))
                    if status_code > -1:
                        span.tag(Tag(key=tags.HttpStatus, val=status_code))
                        if status_code >= 400:
                            span.error_occurred = True

        setattr(handler, 'do_' + method, _sw_do_method)
