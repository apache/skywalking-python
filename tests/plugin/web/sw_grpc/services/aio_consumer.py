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
import socketserver
from http.server import BaseHTTPRequestHandler

import example_pb2
import example_pb2_grpc
import grpc


async def generate_messages():
    yield example_pb2.HelloRequest(name='World')


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa
        async def task():
            async with grpc.aio.insecure_channel('aio_provider:50061') as channel:
                stub = example_pb2_grpc.GreeterStub(channel)
                request = example_pb2.HelloRequest(name='World')
                await stub.SayHello(request)
                async for _ in stub.SayHelloUS(request):
                    pass
                await stub.SayHelloSU(generate_messages())
                async for _ in stub.SayHelloSS(generate_messages()):
                    pass

        asyncio.run(task())
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Hello, world')


if __name__ == '__main__':
    PORT = 50062
    with socketserver.TCPServer(('', PORT), SimpleHTTPRequestHandler) as httpd:
        print('serving at port', PORT)
        httpd.serve_forever()
