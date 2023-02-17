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
from skywalking.trace.context import get_context
from skywalking.trace.tags import TagHttpMethod, TagHttpURL, TagHttpStatusMsg

link_vector = ['https://websockets.readthedocs.io']
support_matrix = {
    'websockets': {
        '>=3.7': ['10.3', '10.4']
    }
}
note = """The websocket instrumentation only traces client side connection handshake,
the actual message exchange (send/recv) is not traced since injecting headers to socket message
body is the only way to propagate the trace context, which requires customization of message structure
and extreme care. (Feel free to add this feature by instrumenting the send/recv methods commented out in the code
by either injecting sw8 headers or propagate the trace context in a separate message)
"""


def install():
    from websockets.legacy.client import WebSocketClientProtocol
    _protocol_handshake_client = WebSocketClientProtocol.handshake

    async def _sw_protocol_handshake_client(self, wsuri,
                                            origin=None,
                                            available_extensions=None,
                                            available_subprotocols=None,
                                            extra_headers=None):

        span = get_context().new_exit_span(op=wsuri.path or '/', peer=f'{wsuri.host}:{wsuri.port}',
                                           component=Component.Websockets)
        with span:
            carrier = span.inject()
            span.layer = Layer.Http
            if not extra_headers and not self.extra_headers:
                # this method actually uses self.extra_headers, not extra_headers
                self.extra_headers = {}
            for item in carrier:
                self.extra_headers[item.key] = item.val

            span.tag(TagHttpMethod('websocket.connect'))

            scheme = 'wss' if wsuri.secure else 'ws'
            span.tag(TagHttpURL(f'{scheme}://{wsuri.host}:{wsuri.port}{wsuri.path}'))
            status_msg = 'connection open'
            try:
                await _protocol_handshake_client(self,
                                                 wsuri=wsuri,
                                                 origin=origin,
                                                 available_extensions=available_extensions,
                                                 available_subprotocols=available_subprotocols,
                                                 extra_headers=extra_headers)
            except Exception as e:
                span.error_occurred = True
                span.log(e)
                status_msg = 'invalid handshake'
                raise e
            finally:
                span.tag(TagHttpStatusMsg(status_msg))

    WebSocketClientProtocol.handshake = _sw_protocol_handshake_client

    # To trace per message transactions
    # _send = WebSocketCommonProtocol.send
    # _recv = WebSocketCommonProtocol.recv
    #
    # async def _sw_send(self, message):
    #     ...
    #     await _send(self, message)
    #
    # async def _sw_recv(self):
    #     ...
    #     await _recv(self)
    #
    # WebSocketCommonProtocol.send = _sw_send
    # WebSocketCommonProtocol.recv = _sw_recv
