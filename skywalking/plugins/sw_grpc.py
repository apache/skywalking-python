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

from asyncio import iscoroutine
from concurrent.futures import Executor
from typing import Any, Awaitable, Callable, List, NamedTuple, Optional, Sequence, Tuple, Union

from skywalking import Component, Layer, config
from skywalking.trace.carrier import Carrier
from skywalking.trace.context import NoopContext, get_context
from skywalking.trace.span import NoopSpan
from skywalking.trace.tags import TagGrpcMethod, TagGrpcStatusCode, TagGrpcUrl

link_vector = ['https://grpc.io/docs/languages/python']
support_matrix = {'grpcio': {'>=3.8': ['1.*']}}
note = """"""


def _get_factory_and_method(rpc_handler: Any) -> Tuple[Callable[..., Any], Callable[..., Any]]:
    import grpc

    if rpc_handler.unary_unary:
        return grpc.unary_unary_rpc_method_handler, rpc_handler.unary_unary
    elif rpc_handler.unary_stream:
        return grpc.unary_stream_rpc_method_handler, rpc_handler.unary_stream
    elif rpc_handler.stream_unary:
        return grpc.stream_unary_rpc_method_handler, rpc_handler.stream_unary
    elif rpc_handler.stream_stream:
        return grpc.stream_stream_rpc_method_handler, rpc_handler.stream_stream
    else:
        raise RuntimeError('RPC handler implementation does not exist')


def _restore_carrier(handler_call_details: Any) -> Carrier:
    metadata_map = dict(handler_call_details.invocation_metadata or ())

    carrier = Carrier()
    for item in carrier:
        val = metadata_map.get(item.key)
        if val is not None:
            item.val = val
    return carrier


def get_method_name(details: Any) -> str:
    method_name = details.method
    if type(method_name) is bytes:
        return method_name.decode()
    if type(method_name) is str:
        return method_name
    return str(method_name)


def install_sync() -> None:
    import grpc
    from grpc import _channel

    def install_server() -> None:
        _grpc_server = grpc.server

        def _make_invoke_intercept_method(
            is_response_streaming: bool,
            next_handler_method: Callable[..., Any],
            handler_call_details: grpc.HandlerCallDetails,
        ) -> Callable[[Any, grpc.ServicerContext], Any]:

            def invoke_intercept_method(request_or_iterator: Any, context: grpc.ServicerContext) -> Any:

                carrier = _restore_carrier(handler_call_details)
                method_name = get_method_name(handler_call_details)
                with (
                    NoopSpan(NoopContext())
                    if config.ignore_grpc_method_check(method_name)
                    else get_context().new_entry_span(op=method_name, carrier=carrier)
                ) as span:
                    span.layer = Layer.RPCFramework
                    span.tag(TagGrpcMethod(method_name))
                    span.component = Component.Grpc
                    span.peer = context.peer()
                    try:
                        return next_handler_method(request_or_iterator, context)
                    except grpc.RpcError as e:
                        if hasattr(e, 'code'):
                            span.tag(TagGrpcStatusCode(e.code()))
                        else:
                            span.tag(TagGrpcStatusCode(grpc.StatusCode.UNKNOWN))
                        span.raised()
                        raise e

            def invoke_intercept_method_response_streaming(
                request_or_iterator: Any, context: grpc.ServicerContext
            ) -> Any:
                carrier = _restore_carrier(handler_call_details)
                method_name = get_method_name(handler_call_details)
                with (
                    NoopSpan(NoopContext())
                    if config.ignore_grpc_method_check(method_name)
                    else get_context().new_entry_span(op=method_name, carrier=carrier)
                ) as span:
                    span.layer = Layer.RPCFramework
                    span.tag(TagGrpcMethod(method_name))
                    span.component = Component.Grpc
                    span.peer = context.peer()
                    try:
                        yield from next_handler_method(request_or_iterator, context)
                    except grpc.RpcError as e:
                        if hasattr(e, 'code'):
                            span.tag(TagGrpcStatusCode(e.code()))
                        else:
                            span.tag(TagGrpcStatusCode(grpc.StatusCode.UNKNOWN))
                        span.raised()
                        raise e

            return invoke_intercept_method_response_streaming if is_response_streaming else invoke_intercept_method

        class ServerInterceptor(grpc.ServerInterceptor):

            def intercept_service(
                self,
                continuation: Callable[[grpc.HandlerCallDetails], grpc.RpcMethodHandler],
                handler_call_details: grpc.HandlerCallDetails,
            ) -> grpc.RpcMethodHandler:
                next_handler = continuation(handler_call_details)

                handler_factory, next_handler_method = _get_factory_and_method(next_handler)

                return handler_factory(
                    _make_invoke_intercept_method(
                        bool(next_handler.response_streaming), next_handler_method, handler_call_details
                    ),
                    request_deserializer=next_handler.request_deserializer,
                    response_serializer=next_handler.response_serializer,
                )

        def _sw_grpc_server(
            thread_pool: Optional[Executor] = None,
            handlers: Optional[Sequence[grpc.GenericRpcHandler]] = None,
            interceptors: Optional[Sequence[Any]] = None,
            options: Optional[Any] = None,
            maximum_concurrent_rpcs: Optional[int] = None,
            compression: Optional[grpc.Compression] = None,
            xds: bool = False,
        ):
            _sw_interceptors = [ServerInterceptor()]
            if interceptors is not None:
                _sw_interceptors.extend(interceptors)
            return _grpc_server(
                thread_pool,
                handlers,
                _sw_interceptors,
                options,
                maximum_concurrent_rpcs,
                compression,
                xds,
            )

        grpc.server = _sw_grpc_server

    def install_client() -> None:
        _grpc_channel = _channel.Channel

        class _ClientCallDetails(NamedTuple):
            method: str
            timeout: Optional[float]
            metadata: Optional[Sequence[Tuple[str, Union[str, bytes]]]]
            credentials: Optional[grpc.CallCredentials]
            wait_for_ready: Optional[bool]
            compression: Any

        class _SWClientCallDetails(_ClientCallDetails, grpc.ClientCallDetails):
            pass

        class _ClientInterceptor(
            grpc.UnaryUnaryClientInterceptor,
            grpc.UnaryStreamClientInterceptor,
            grpc.StreamUnaryClientInterceptor,
            grpc.StreamStreamClientInterceptor,
        ):
            def __init__(self, target: str):
                self.target = target

            def _intercept(
                self,
                continuation: Callable[..., Any],
                client_call_details: grpc.ClientCallDetails,
                request: Any,
            ):
                method_name = get_method_name(client_call_details)
                with (
                    NoopSpan(NoopContext())
                    if config.ignore_grpc_method_check(method_name)
                    else get_context().new_exit_span(op=method_name, peer=self.target, component=Component.Grpc)
                ) as span:
                    span.layer = Layer.RPCFramework
                    span.tag(TagGrpcMethod(method_name))
                    span.tag(TagGrpcUrl(self.target))
                    carrier = span.inject()
                    metadata = list(client_call_details.metadata or [])
                    for item in carrier:
                        metadata.append((item.key, item.val))
                    new_client_call_details = _SWClientCallDetails(
                        client_call_details.method,
                        client_call_details.timeout,
                        metadata,
                        client_call_details.credentials,
                        client_call_details.wait_for_ready,
                        client_call_details.compression,
                    )
                    return continuation(new_client_call_details, request)

            def intercept_unary_unary(self, continuation, client_call_details, request):
                return self._intercept(continuation, client_call_details, request)

            def intercept_unary_stream(self, continuation, client_call_details, request):
                return self._intercept(continuation, client_call_details, request)

            def intercept_stream_unary(self, continuation, client_call_details, request_iterator):
                return self._intercept(continuation, client_call_details, request_iterator)

            def intercept_stream_stream(self, continuation, client_call_details, request_iterator):
                return self._intercept(continuation, client_call_details, request_iterator)

        def _sw_grpc_channel_factory(target: str, *args: Any, **kwargs: Any):
            c = _grpc_channel(target, *args, **kwargs)
            if target == config.agent_collector_backend_services:
                return c
            return grpc.intercept_channel(c, _ClientInterceptor(target))

        _channel.Channel = _sw_grpc_channel_factory

    install_client()
    install_server()


def install_async() -> None:
    import grpc
    from grpc.aio import _channel as _aio_channel

    def install_async_server() -> None:
        _grpc_aio_server = grpc.aio.server

        def _make_invoke_intercept_method(
            is_response_streaming: bool,
            next_handler_method: Callable[..., Any],
            handler_call_details: grpc.HandlerCallDetails,
        ) -> Callable[[Any, grpc.aio.ServicerContext[Any, Any]], Awaitable[Any]]:

            async def invoke_intercept_method(
                request_or_iterator: Any, context: grpc.aio.ServicerContext[Any, Any]
            ) -> Any:

                carrier = _restore_carrier(handler_call_details)
                method_name = get_method_name(handler_call_details)
                with (
                    NoopSpan(NoopContext())
                    if config.ignore_grpc_method_check(method_name)
                    else get_context().new_entry_span(op=method_name, carrier=carrier)
                ) as span:
                    span.layer = Layer.RPCFramework
                    span.tag(TagGrpcMethod(method_name))
                    span.component = Component.Grpc
                    span.peer = context.peer()
                    try:
                        return await next_handler_method(request_or_iterator, context)
                    except grpc.RpcError as e:
                        if hasattr(e, 'code'):
                            span.tag(TagGrpcStatusCode(e.code()))
                        else:
                            span.tag(TagGrpcStatusCode(grpc.StatusCode.UNKNOWN))
                        span.raised()
                        raise e

            async def invoke_intercept_method_response_streaming(
                request_or_iterator: Any, context: grpc.aio.ServicerContext[Any, Any]
            ) -> Any:
                carrier = _restore_carrier(handler_call_details)
                method_name = get_method_name(handler_call_details)
                with (
                    NoopSpan(NoopContext())
                    if config.ignore_grpc_method_check(method_name)
                    else get_context().new_entry_span(op=method_name, carrier=carrier)
                ) as span:
                    span.layer = Layer.RPCFramework
                    span.tag(TagGrpcMethod(method_name))
                    span.component = Component.Grpc
                    span.peer = context.peer()
                    try:
                        coroutine_or_asyncgen = next_handler_method(request_or_iterator, context)
                        async for r in (
                            await coroutine_or_asyncgen if iscoroutine(coroutine_or_asyncgen) else coroutine_or_asyncgen
                        ):
                            yield r
                    except grpc.RpcError as e:
                        if hasattr(e, 'code'):
                            span.tag(TagGrpcStatusCode(e.code()))
                        else:
                            span.tag(TagGrpcStatusCode(grpc.StatusCode.UNKNOWN))
                        span.raised()
                        raise e

            return invoke_intercept_method_response_streaming if is_response_streaming else invoke_intercept_method

        class ServerInterceptor(grpc.aio.ServerInterceptor):

            async def intercept_service(
                self,
                continuation: Callable[[grpc.HandlerCallDetails], Awaitable[grpc.RpcMethodHandler]],
                handler_call_details: grpc.HandlerCallDetails,
            ) -> grpc.RpcMethodHandler:
                next_handler = await continuation(handler_call_details)

                handler_factory, next_handler_method = _get_factory_and_method(next_handler)
                return handler_factory(
                    _make_invoke_intercept_method(
                        bool(next_handler.response_streaming), next_handler_method, handler_call_details
                    ),
                    request_deserializer=next_handler.request_deserializer,
                    response_serializer=next_handler.response_serializer,
                )

        def _sw_grpc_aio_server(
            migration_thread_pool: Optional[Executor] = None,
            handlers: Optional[Sequence[grpc.GenericRpcHandler]] = None,
            interceptors: Optional[Sequence[Any]] = None,
            options: Optional[grpc.aio.ChannelArgumentType] = None,
            maximum_concurrent_rpcs: Optional[int] = None,
            compression: Optional[grpc.Compression] = None,
        ):
            _sw_interceptors = [ServerInterceptor()]
            if interceptors is not None:
                _sw_interceptors.extend(interceptors)
            return _grpc_aio_server(
                migration_thread_pool,
                handlers,
                _sw_interceptors,
                options,
                maximum_concurrent_rpcs,
                compression,
            )

        grpc.aio.server = _sw_grpc_aio_server

    def install_async_client() -> None:
        _aio_grpc_channel = _aio_channel.Channel

        class _AioClientCallDetails(NamedTuple):
            method: str
            timeout: Optional[float]
            metadata: Optional[grpc.aio.Metadata]
            credentials: Optional[grpc.CallCredentials]
            wait_for_ready: Optional[bool]

        class _SWAioClientCallDetails(_AioClientCallDetails, grpc.aio.ClientCallDetails):
            pass

        class _AioClientInterceptor:
            def __init__(self, target: str):
                self.target = target

            async def _intercept(
                self,
                continuation: Callable[..., Any],
                client_call_details: grpc.aio.ClientCallDetails,
                request: Any,
            ):
                method_name = get_method_name(client_call_details)
                span = (
                    NoopSpan(NoopContext())
                    if config.ignore_grpc_method_check(method_name)
                    else get_context().new_exit_span(op=method_name, peer=self.target, component=Component.Grpc)
                )
                with span:
                    span.layer = Layer.RPCFramework
                    span.tag(TagGrpcMethod(method_name))
                    span.tag(TagGrpcUrl(self.target))
                    carrier = span.inject()
                    metadata = client_call_details.metadata or grpc.aio.Metadata()
                    for item in carrier:
                        metadata.add(item.key, item.val)
                    new_client_call_details = _SWAioClientCallDetails(
                        client_call_details.method,
                        client_call_details.timeout,
                        metadata,
                        client_call_details.credentials,
                        client_call_details.wait_for_ready,
                    )
                    return await continuation(new_client_call_details, request)

        class _AioClientUnaryUnaryInterceptor(_AioClientInterceptor, grpc.aio.UnaryUnaryClientInterceptor):

            async def intercept_unary_unary(
                self,
                continuation: Callable[
                    [grpc.aio.ClientCallDetails, grpc.aio._typing.RequestType], grpc.aio._call.UnaryUnaryCall
                ],
                client_call_details: grpc.aio.ClientCallDetails,
                request: grpc.aio._typing.RequestType,
            ) -> grpc.aio._call.UnaryUnaryCall:
                return await self._intercept(continuation, client_call_details, request)

        class _AioClientUnaryStreamInterceptor(_AioClientInterceptor, grpc.aio.UnaryStreamClientInterceptor):

            async def intercept_unary_stream(
                self,
                continuation: Callable[
                    [grpc.aio.ClientCallDetails, grpc.aio._typing.RequestType], grpc.aio._call.UnaryStreamCall
                ],
                client_call_details: grpc.aio.ClientCallDetails,
                request: grpc.aio._typing.RequestType,
            ) -> grpc.aio._call.UnaryStreamCall:
                return await self._intercept(continuation, client_call_details, request)

        class _AioClientStreamUnaryInterceptor(_AioClientInterceptor, grpc.aio.StreamUnaryClientInterceptor):

            async def intercept_stream_unary(
                self,
                continuation: Callable[
                    [grpc.aio.ClientCallDetails, grpc.aio._typing.RequestType], grpc.aio._call.StreamUnaryCall
                ],
                client_call_details: grpc.aio.ClientCallDetails,
                request_iterator: grpc.aio._typing.RequestIterableType,
            ) -> grpc.aio._call.StreamUnaryCall:
                return await self._intercept(continuation, client_call_details, request_iterator)

        class _AioClientStreamStreamInterceptor(_AioClientInterceptor, grpc.aio.StreamStreamClientInterceptor):

            async def intercept_stream_stream(
                self,
                continuation: Callable[
                    [grpc.aio.ClientCallDetails, grpc.aio._typing.RequestType], grpc.aio._call.StreamStreamCall
                ],
                client_call_details: grpc.aio.ClientCallDetails,
                request_iterator: grpc.aio._typing.RequestIterableType,
            ) -> grpc.aio._call.StreamStreamCall:
                return await self._intercept(continuation, client_call_details, request_iterator)

        def _sw_grpc_aio_channel_factory(
            target: str,
            options: grpc.aio.ChannelArgumentType,
            credentials: Optional[grpc.ChannelCredentials],
            compression: Optional[grpc.Compression],
            interceptors: Optional[Sequence[grpc.aio.ClientInterceptor]],
        ):
            if target == config.agent_collector_backend_services:
                return _aio_grpc_channel(target, options, credentials, compression, interceptors)
            _sw_interceptors: List[grpc.aio.ClientInterceptor] = [
                _AioClientUnaryUnaryInterceptor(target),
                _AioClientUnaryStreamInterceptor(target),
                _AioClientStreamUnaryInterceptor(target),
                _AioClientStreamStreamInterceptor(target),
            ]
            _sw_interceptors.extend(interceptors or [])
            return _aio_grpc_channel(target, options, credentials, compression, _sw_interceptors)

        _aio_channel.Channel = _sw_grpc_aio_channel_factory

    install_async_client()
    install_async_server()


def install():
    install_sync()
    install_async()
