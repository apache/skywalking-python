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
from skywalking.loggings import logger
from skywalking.trace.carrier import Carrier
from skywalking.trace.tags import TagHttpMethod, TagHttpURL, TagHttpStatusCode

link_vector = ['https://www.odoo.com/documentation/13.0/']
support_matrix = {
    'odoo': {
        '>=3.10': ['13.0']
    }
}
note = """"""


def install():
    from odoo.http import Root

    if getattr(Root, '_sw_odoo_wrapped', False):
        return

    _dispatch = Root.dispatch

    def _sw_dispatch(this, environ, start_response):
        try:
            method = environ.get('REQUEST_METHOD', '')
            path = environ.get('PATH_INFO') or '/'
            carrier = _carrier_from_environ(environ)
            status_code = [-1]

            def _sw_start_response(status, response_headers, exc_info=None):
                status_code[0] = _parse_status_code(status)
                if exc_info is not None:
                    try:
                        return start_response(status, response_headers, exc_info)
                    except TypeError:
                        return start_response(status, response_headers)
                return start_response(status, response_headers)

            span = _new_noop_span() if config.ignore_http_method_check(method) \
                else get_context().new_entry_span(op=path, carrier=carrier, inherit=Component.General)
        except Exception:
            _log_tracing_exception('SkyWalking Odoo tracing setup failed, dispatch without tracing.')
            return _dispatch(this, environ, start_response)

        if not _safe_enter_span(span):
            return _dispatch(this, environ, start_response)

        exc_info = (None, None, None)
        try:
            _safe_prepare_span(span, environ, method, path)
            try:
                return _dispatch(this, environ, _sw_start_response)
            except Exception:
                import sys
                exc_info = sys.exc_info()
                raise
            finally:
                _safe_tag_status(span, status_code[0])
        finally:
            _safe_exit_span(span, exc_info)

    Root.dispatch = _sw_dispatch
    Root._sw_odoo_wrapped = True


def get_context():
    from skywalking.trace.context import get_context as _get_context
    return _get_context()


def _safe_enter_span(span):
    try:
        span.__enter__()
        return True
    except Exception:
        _log_tracing_exception('SkyWalking Odoo span start failed, dispatch without tracing.')
        return False


def _safe_exit_span(span, exc_info):
    try:
        span.__exit__(*exc_info)
    except Exception:
        _log_tracing_exception('SkyWalking Odoo span stop failed.')


def _safe_prepare_span(span, environ, method, path):
    try:
        span.layer = Layer.Http
        span.component = Component.Odoo
        span.peer = _peer_from_environ(environ)
    except Exception:
        _log_tracing_exception('SkyWalking Odoo span attribute setup failed.')

    _safe_tag(span, lambda: TagHttpMethod(method))
    _safe_tag(span, lambda: TagHttpURL(_url_from_environ(environ, path)))


def _safe_tag_status(span, status_code):
    if status_code <= -1:
        return

    _safe_tag(span, lambda: TagHttpStatusCode(status_code))
    if status_code >= 400:
        try:
            span.error_occurred = True
        except Exception:
            _log_tracing_exception('SkyWalking Odoo span error flag setup failed.')


def _safe_tag(span, tag_factory):
    try:
        span.tag(tag_factory())
    except Exception:
        _log_tracing_exception('SkyWalking Odoo span tag setup failed.')


def _log_tracing_exception(message):
    try:
        logger.debug(message, exc_info=True)
    except Exception:
        pass


def _new_noop_span():
    from skywalking.trace.context import NoopContext
    from skywalking.trace.span import NoopSpan
    return NoopSpan(NoopContext())


def _carrier_from_environ(environ):
    carrier = Carrier()
    for item in carrier:
        key = 'HTTP_' + item.key.upper().replace('-', '_')
        if key in environ:
            item.val = environ[key]
    if carrier.is_suppressed:
        return Carrier(correlation=carrier.correlation_carrier.correlation)
    return carrier


def _peer_from_environ(environ):
    remote_addr = environ.get('REMOTE_ADDR')
    remote_port = environ.get('REMOTE_PORT') or '80'
    return f'{remote_addr}:{remote_port}' if remote_addr else ''


def _url_from_environ(environ, path):
    scheme = environ.get('wsgi.url_scheme') or 'http'
    host = environ.get('HTTP_HOST') or environ.get('SERVER_NAME') or ''
    return f'{scheme}://{host}{path}' if host else path


def _parse_status_code(status):
    try:
        return int(str(status).split(' ', 1)[0])
    except (TypeError, ValueError):
        return -1
