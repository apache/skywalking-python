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

import asyncio
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import AsyncMock, MagicMock, patch

from skywalking import config


class _OkHandler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa
        length = int(self.headers.get('Content-Length') or 0)
        self.rfile.read(length)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{}')

    def log_message(self, *_args):
        pass


def _start_http_server():
    server = HTTPServer(('127.0.0.1', 0), _OkHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


class TestAsyncHttpClientSession(unittest.TestCase):
    def setUp(self):
        self._saved = (
            config.agent_collector_backend_services,
            config.agent_protocol,
            config.agent_name,
            config.agent_instance_name,
        )
        config.agent_protocol = 'http'
        config.agent_name = 'test-service'
        config.agent_instance_name = 'test-instance'

    def tearDown(self):
        (
            config.agent_collector_backend_services,
            config.agent_protocol,
            config.agent_name,
            config.agent_instance_name,
        ) = self._saved

    def test_async_http_session_survives_repeated_posts(self):
        """async with session.post closes the response, not the long-lived session."""
        server, port = _start_http_server()
        config.agent_collector_backend_services = f'127.0.0.1:{port}'
        try:
            from skywalking.client.http_aio import HttpServiceManagementClientAsync

            async def run():
                client = HttpServiceManagementClientAsync()
                self.assertFalse(client.client.closed)
                await client.send_instance_props()
                self.assertFalse(
                    client.client.closed,
                    'ClientSession must stay open after the first request',
                )
                await client.send_heart_beat()
                self.assertFalse(client.client.closed)
                await client.aclose()
                self.assertTrue(client.client.closed)

            asyncio.run(run())
        finally:
            server.shutdown()

    def test_async_http_segment_reporter_reuses_session(self):
        server, port = _start_http_server()
        config.agent_collector_backend_services = f'127.0.0.1:{port}'
        try:
            from skywalking.client.http_aio import HttpTraceSegmentReportServiceAsync

            class _Seg:
                related_traces = ['t1']
                segment_id = 's1'
                is_size_limited = False
                spans = []

            async def gen():
                yield _Seg()
                yield _Seg()

            async def run():
                reporter = HttpTraceSegmentReportServiceAsync()
                await reporter.report(gen())
                self.assertFalse(reporter.client.closed)
                await reporter.aclose()

            asyncio.run(run())
        finally:
            server.shutdown()

    def test_async_http_heartbeat_with_aiohttp_plugin_installed(self):
        from aiohttp import ClientSession
        from aiohttp.web_protocol import RequestHandler

        from skywalking.agent.protocol.http_aio import HttpProtocolAsync
        from skywalking.plugins import sw_aiohttp

        self.addCleanup(setattr, ClientSession, '_request', ClientSession._request)
        self.addCleanup(setattr, RequestHandler, '_handle_request', RequestHandler._handle_request)
        sw_aiohttp.install()

        server, port = _start_http_server()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        config.agent_collector_backend_services = f'127.0.0.1:{port}'

        async def run():
            protocol = HttpProtocolAsync()
            sessions = [part.client for part in (
                protocol.service_management, protocol.traces_reporter, protocol.log_reporter,
            )]
            try:
                await asyncio.wait_for(protocol.heartbeat(), timeout=5)
                await asyncio.wait_for(protocol.heartbeat(), timeout=5)
                self.assertTrue(all(not session.closed for session in sessions))
            finally:
                await protocol.aclose()
            self.assertTrue(all(session.closed for session in sessions))

        with patch.object(_OkHandler, 'do_POST', autospec=True, side_effect=_OkHandler.do_POST) as post, \
                patch.object(sw_aiohttp, 'get_context') as get_context, \
                patch.object(config, 'agent_collector_properties_report_period_factor', 10):
            asyncio.run(run())
            self.assertEqual(post.call_count, 3)
            get_context.assert_not_called()


class TestAiohttpServerCollectorSkip(unittest.TestCase):
    """RequestHandler skip must await the original handler, not return the function."""

    def setUp(self):
        self._saved = (
            config.agent_collector_backend_services,
            config.agent_protocol,
        )
        config.agent_protocol = 'http'
        config.agent_collector_backend_services = '127.0.0.1:12800'

    def tearDown(self):
        (
            config.agent_collector_backend_services,
            config.agent_protocol,
        ) = self._saved

    def test_collector_host_skip_awaits_original_handler(self):
        from aiohttp import ClientSession
        from aiohttp.web_protocol import RequestHandler

        from skywalking.plugins import sw_aiohttp

        self.addCleanup(setattr, ClientSession, '_request', ClientSession._request)
        self.addCleanup(setattr, RequestHandler, '_handle_request', RequestHandler._handle_request)

        stub = AsyncMock(return_value=('resp', False))
        RequestHandler._handle_request = stub
        sw_aiohttp.install()

        handler = MagicMock()
        request = MagicMock()
        request.url.host = '127.0.0.1'
        request.url.port = 12800

        async def run():
            with patch.object(sw_aiohttp, 'get_context') as get_context:
                result = await RequestHandler._handle_request(handler, request, 1.5, extra=True)
                get_context.assert_not_called()
                return result

        result = asyncio.run(run())
        self.assertEqual(('resp', False), result)
        stub.assert_awaited_once_with(handler, request, 1.5, extra=True)

    def test_non_collector_host_still_creates_entry_span(self):
        from aiohttp import ClientSession
        from aiohttp.web_protocol import RequestHandler

        from skywalking.plugins import sw_aiohttp

        self.addCleanup(setattr, ClientSession, '_request', ClientSession._request)
        self.addCleanup(setattr, RequestHandler, '_handle_request', RequestHandler._handle_request)

        resp = MagicMock()
        resp.status = 200
        stub = AsyncMock(return_value=(resp, False))
        RequestHandler._handle_request = stub
        sw_aiohttp.install()

        handler = MagicMock()
        request = MagicMock()
        request.url.host = '127.0.0.1'
        request.url.port = 9999
        request.method = 'GET'
        request.path = '/users'
        request.headers = {}
        request._transport_peername = ('10.0.0.1', 1234)
        request.scheme = 'http'
        request.host = '127.0.0.1:9999'

        span = MagicMock()
        context = MagicMock()
        context.new_entry_span.return_value = span

        async def run():
            with patch.object(sw_aiohttp, 'get_context', return_value=context):
                return await RequestHandler._handle_request(handler, request, 0.0)

        result = asyncio.run(run())
        self.assertEqual((resp, False), result)
        context.new_entry_span.assert_called_once()
        stub.assert_awaited_once()


if __name__ == '__main__':
    unittest.main()
