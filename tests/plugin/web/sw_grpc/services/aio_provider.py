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
from concurrent import futures
from typing import Any, AsyncGenerator, AsyncIterable, Tuple

import example_pb2
import example_pb2_grpc
import grpc


async def async_enumerate(aiterable: AsyncIterable[Any], start: int = 0) -> AsyncGenerator[Tuple[int, Any], Any]:
    index = start
    async for item in aiterable:
        yield index, item
        index += 1


class GreeterServicer(example_pb2_grpc.GreeterServicer):
    async def SayHello(self, request, context):  # noqa
        return example_pb2.HelloReply()

    async def SayHelloUS(self, request, context):  # noqa
        for i in range(3):
            response = example_pb2.HelloReply()
            response.message = f'Hello, {request.name} {i}!'
            yield response

    async def SayHelloSU(self, request_iterator, context):  # noqa
        response = example_pb2.HelloReply()
        async for request in request_iterator:
            response.message = f'Hello, {request.name}!'
        return response

    async def SayHelloSS(self, request_iterator, context):  # noqa
        async for i, request in async_enumerate(request_iterator):
            response = example_pb2.HelloReply()
            response.message = f'Hello, {request.name} {i}!'
            yield response


async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    example_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    server.add_insecure_port('[::]:50061')
    await server.start()
    await server.wait_for_termination()


if __name__ == '__main__':
    asyncio.run(serve())
