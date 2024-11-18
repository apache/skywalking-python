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

from concurrent import futures

import example_pb2
import example_pb2_grpc
import grpc


class GreeterServicer(example_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):  # noqa
        return example_pb2.HelloReply()

    def SayHelloUS(self, request, context):  # noqa
        for i in range(3):
            response = example_pb2.HelloReply()
            response.message = f'Hello, {request.name} {i}!'
            yield response

    def SayHelloSU(self, request_iterator, context):  # noqa
        response = example_pb2.HelloReply()
        for request in request_iterator:
            response.message = f'Hello, {request.name}!'
        return response

    def SayHelloSS(self, request_iterator, context):  # noqa
        for i, request in enumerate(request_iterator):
            response = example_pb2.HelloReply()
            response.message = f'Hello, {request.name} {i}!'
            yield response


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    example_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
