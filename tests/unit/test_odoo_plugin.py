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

import sys
import types
import unittest

from skywalking import Component, Layer, config
from skywalking.plugins import sw_odoo


class FakeSpan:
    def __init__(self, op, carrier):
        self.op = op
        self.carrier = carrier
        self.layer = None
        self.component = None
        self.peer = None
        self.tags = []
        self.error_occurred = False
        self.raised_called = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, Exception):
            self.raised()
        return False

    def tag(self, tag):
        self.tags.append((tag.key, tag.val))
        return self

    def raised(self):
        self.raised_called = True
        self.error_occurred = True
        return self


class FakeContext:
    def __init__(self):
        self.spans = []

    def new_entry_span(self, op, carrier=None, inherit=None):
        span = FakeSpan(op, carrier)
        self.spans.append(span)
        return span


class FakeRoot:
    def dispatch(self, environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b'ok']


class TestOdooPlugin(unittest.TestCase):
    def setUp(self):
        self.modules = sys.modules.copy()
        self.original_ignore = config.RE_HTTP_IGNORE_METHOD
        self.fake_context = FakeContext()
        self.original_get_context = sw_odoo.get_context
        sw_odoo.get_context = lambda: self.fake_context

        odoo_module = types.ModuleType('odoo')
        http_module = types.ModuleType('odoo.http')
        http_module.Root = FakeRoot
        odoo_module.http = http_module
        sys.modules['odoo'] = odoo_module
        sys.modules['odoo.http'] = http_module

    def tearDown(self):
        sys.modules.clear()
        sys.modules.update(self.modules)
        config.RE_HTTP_IGNORE_METHOD = self.original_ignore
        sw_odoo.get_context = self.original_get_context

    def test_dispatch_creates_http_entry_span(self):
        sw_odoo.install()
        root = sys.modules['odoo.http'].Root()
        status = []

        result = root.dispatch({
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/web/login',
            'QUERY_STRING': 'debug=1',
            'HTTP_HOST': 'odoo.example.com',
            'REMOTE_ADDR': '10.0.0.5',
            'REMOTE_PORT': '45678',
            'HTTP_SW8': 'bad-carrier',
            'HTTP_SW8_CORRELATION': 'dGVuYW50:ZWM=',
        }, lambda value, headers, exc_info=None: status.append(value))

        self.assertEqual([b'ok'], result)
        self.assertEqual(['200 OK'], status)
        self.assertEqual(1, len(self.fake_context.spans))
        span = self.fake_context.spans[0]
        self.assertEqual('/web/login', span.op)
        self.assertEqual(Layer.Http, span.layer)
        self.assertEqual(Component.Odoo, span.component)
        self.assertEqual('10.0.0.5:45678', span.peer)
        self.assertIn(('http.method', 'GET'), span.tags)
        self.assertIn(('http.url', 'http://odoo.example.com/web/login'), span.tags)
        self.assertIn(('http.status_code', '200'), span.tags)
        self.assertFalse(span.carrier.is_suppressed)
        self.assertFalse(span.carrier.is_valid)
        self.assertEqual({'tenant': 'ec'}, span.carrier.correlation_carrier.correlation)

    def test_invalid_sw8_header_does_not_suppress_odoo_entry_span(self):
        carrier = sw_odoo._carrier_from_environ({
            'HTTP_SW8': 'bad-carrier',
            'HTTP_SW8_CORRELATION': 'dGVuYW50:ZWM=',
        })

        self.assertFalse(carrier.is_suppressed)
        self.assertFalse(carrier.is_valid)
        self.assertEqual({'tenant': 'ec'}, carrier.correlation_carrier.correlation)

    def test_dispatch_supports_odoo_two_argument_start_response_wrapper(self):
        sw_odoo.install()
        root = sys.modules['odoo.http'].Root()
        status = []

        result = root.dispatch(
            {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/web/login'},
            lambda value, headers: status.append(value),
        )

        self.assertEqual([b'ok'], result)
        self.assertEqual(['200 OK'], status)

    def test_dispatch_supports_two_argument_start_response_wrapper_with_exc_info(self):
        class ExcInfoRoot:
            def dispatch(self, environ, start_response):
                start_response('500 Internal Server Error', [], (RuntimeError, RuntimeError('boom'), None))
                return [b'error']

        sys.modules['odoo.http'].Root = ExcInfoRoot
        sw_odoo.install()
        root = sys.modules['odoo.http'].Root()
        status = []

        result = root.dispatch(
            {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/web/login'},
            lambda value, headers: status.append(value),
        )

        self.assertEqual([b'error'], result)
        self.assertEqual(['500 Internal Server Error'], status)

    def test_dispatch_falls_back_to_odoo_when_tracing_setup_fails(self):
        sw_odoo.get_context = lambda: (_ for _ in ()).throw(RuntimeError('trace failed'))
        sw_odoo.install()
        root = sys.modules['odoo.http'].Root()
        status = []

        result = root.dispatch(
            {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/web/login'},
            lambda value, headers: status.append(value),
        )

        self.assertEqual([b'ok'], result)
        self.assertEqual(['200 OK'], status)
        self.assertEqual([], self.fake_context.spans)

    def test_dispatch_falls_back_to_odoo_when_span_start_fails(self):
        class FailingStartSpan(FakeSpan):
            def __enter__(self):
                raise RuntimeError('span start failed')

        class FailingStartContext(FakeContext):
            def new_entry_span(self, op, carrier=None, inherit=None):
                return FailingStartSpan(op, carrier)

        self.fake_context = FailingStartContext()
        sw_odoo.install()
        root = sys.modules['odoo.http'].Root()
        status = []

        result = root.dispatch(
            {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/web/login'},
            lambda value, headers: status.append(value),
        )

        self.assertEqual([b'ok'], result)
        self.assertEqual(['200 OK'], status)

    def test_dispatch_marks_http_errors(self):
        class ErrorRoot:
            def dispatch(self, environ, start_response):
                start_response('500 Internal Server Error', [])
                return [b'error']

        sys.modules['odoo.http'].Root = ErrorRoot
        sw_odoo.install()

        root = sys.modules['odoo.http'].Root()
        root.dispatch({'REQUEST_METHOD': 'POST', 'PATH_INFO': '/web/dataset/call_kw'}, lambda *_: None)

        span = self.fake_context.spans[0]
        self.assertTrue(span.error_occurred)
        self.assertIn(('http.status_code', '500'), span.tags)

    def test_dispatch_records_exceptions_and_reraises(self):
        class RaisingRoot:
            def dispatch(self, environ, start_response):
                raise RuntimeError('boom')

        sys.modules['odoo.http'].Root = RaisingRoot
        sw_odoo.install()

        root = sys.modules['odoo.http'].Root()
        with self.assertRaises(RuntimeError):
            root.dispatch({'REQUEST_METHOD': 'GET', 'PATH_INFO': '/boom'}, lambda *_: None)

        self.assertTrue(self.fake_context.spans[0].raised_called)


if __name__ == '__main__':
    unittest.main()
