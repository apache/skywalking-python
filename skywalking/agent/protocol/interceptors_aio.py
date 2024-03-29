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

from collections import namedtuple

import grpc


class _ClientInterceptorAsync(
    grpc.aio.UnaryUnaryClientInterceptor,
    grpc.aio.UnaryStreamClientInterceptor,
    grpc.aio.StreamUnaryClientInterceptor,
    grpc.aio.StreamStreamClientInterceptor
):

    def __init__(self, interceptor_async_function):
        self._fn = interceptor_async_function

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        new_details, new_request_iterator, postprocess = await \
            self._fn(client_call_details, iter((request,)), False, False)
        response = await continuation(new_details, next(new_request_iterator))
        return (await postprocess(response)) if postprocess else response

    async def intercept_unary_stream(self, continuation, client_call_details, request):
        new_details, new_request_iterator, postprocess = await \
            self._fn(client_call_details, iter((request,)), False, True)
        response_it = await continuation(new_details, next(new_request_iterator))
        return (await postprocess(response_it)) if postprocess else response_it

    async def intercept_stream_unary(self, continuation, client_call_details, request_iterator):
        new_details, new_request_iterator, postprocess = await \
            self._fn(client_call_details, request_iterator, True, False)
        response = await continuation(new_details, new_request_iterator)
        return (await postprocess(response)) if postprocess else response

    async def intercept_stream_stream(self, continuation, client_call_details, request_iterator):
        new_details, new_request_iterator, postprocess = await \
            self._fn(client_call_details, request_iterator, True, True)
        response_it = await continuation(new_details, new_request_iterator)
        return (await postprocess(response_it)) if postprocess else response_it


def create(intercept_async_call):
    return _ClientInterceptorAsync(intercept_async_call)


ClientCallDetails = namedtuple('ClientCallDetails', ('method', 'timeout', 'metadata', 'credentials'))


def header_adder_interceptor_async(header, value):
    async def intercept_async_call(client_call_details, request_iterator, request_streaming, response_streaming):
        metadata = list(client_call_details.metadata or ())
        metadata.append((header, value))
        client_call_details = ClientCallDetails(
            client_call_details.method, client_call_details.timeout, metadata, client_call_details.credentials,
        )
        return client_call_details, request_iterator, None

    return create(intercept_async_call)
