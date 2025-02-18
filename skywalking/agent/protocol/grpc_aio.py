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

import logging
import traceback
from asyncio import Queue, Event

import grpc

from skywalking import config
from skywalking.agent.protocol import ProtocolAsync
from skywalking.agent.protocol.interceptors_aio import header_adder_interceptor_async
from skywalking.client.grpc_aio import GrpcServiceManagementClientAsync, GrpcTraceSegmentReportServiceAsync, \
    GrpcProfileTaskChannelServiceAsync, GrpcLogReportServiceAsync, GrpcMeterReportServiceAsync
from skywalking.loggings import logger, logger_debug_enabled
from skywalking.profile.profile_task import ProfileTask
from skywalking.profile.snapshot import TracingThreadSnapshot
from skywalking.protocol.common.Common_pb2 import KeyStringValuePair
from skywalking.protocol.language_agent.Tracing_pb2 import SegmentObject, SpanObject, Log, SegmentReference
from skywalking.protocol.logging.Logging_pb2 import LogData
from skywalking.protocol.language_agent.Meter_pb2 import MeterData
from skywalking.protocol.profile.Profile_pb2 import ThreadSnapshot, ThreadStack
from skywalking.trace.segment import Segment


class GrpcProtocolAsync(ProtocolAsync):
    """
    grpc for asyncio
    """
    def __init__(self):
        self.properties_sent = Event()

        # grpc.aio.channel do not have subscribe() method to set a callback when channel state changed
        # instead, it has wait_for_state_change()/get_state() method to get the current state of the channel
        # since here is an inherent race between the invocation of `wait_for_state_change` and `get_state`,
        # and the channel state is only used for debug, the cost of monitoring this value is too high to support.
        # self.state = None

        interceptors = None
        if config.agent_authentication:
            interceptors = [header_adder_interceptor_async('authentication', config.agent_authentication)]

        if config.agent_force_tls:
            self.channel = grpc.aio.secure_channel(config.agent_collector_backend_services,
                                                   grpc.ssl_channel_credentials(), interceptors=interceptors)
        else:
            self.channel = grpc.aio.insecure_channel(config.agent_collector_backend_services,
                                                     interceptors=interceptors)

        self.service_management = GrpcServiceManagementClientAsync(self.channel)
        self.traces_reporter = GrpcTraceSegmentReportServiceAsync(self.channel)
        self.log_reporter = GrpcLogReportServiceAsync(self.channel)
        self.meter_reporter = GrpcMeterReportServiceAsync(self.channel)
        self.profile_channel = GrpcProfileTaskChannelServiceAsync(self.channel)

    async def query_profile_commands(self):
        if logger_debug_enabled:
            logger.debug('query profile commands')
        await self.profile_channel.do_query()

    async def notify_profile_task_finish(self, task: ProfileTask):
        await self.profile_channel.finish(task)

    async def heartbeat(self):
        try:
            if not self.properties_sent.is_set():
                await self.service_management.send_instance_props()
                self.properties_sent.set()

            await self.service_management.send_heart_beat()

        except grpc.aio.AioRpcError:
            self.on_error()
            raise

    def on_error(self):
        if logger_debug_enabled:
            logger.debug('error occurred in grpc protocol (Async)')
        traceback.print_exc() if logger.isEnabledFor(logging.DEBUG) else None

    async def report_segment(self, queue: Queue):
        async def generator():
            while True:
                # Let eventloop schedule blocking instead of user configuration: `config.agent_queue_timeout`
                segment = await queue.get()  # type: Segment

                queue.task_done()

                if logger_debug_enabled:
                    logger.debug('reporting segment %s', segment)

                s = SegmentObject(
                    traceId=str(segment.related_traces[0]),
                    traceSegmentId=str(segment.segment_id),
                    service=config.agent_name,
                    serviceInstance=config.agent_instance_name,
                    isSizeLimited=segment.is_size_limited,
                    spans=[SpanObject(
                        spanId=span.sid,
                        parentSpanId=span.pid,
                        startTime=span.start_time,
                        endTime=span.end_time,
                        operationName=span.op,
                        peer=span.peer,
                        spanType=span.kind.name,
                        spanLayer=span.layer.name,
                        componentId=span.component.value,
                        isError=span.error_occurred,
                        logs=[Log(
                            time=int(log.timestamp * 1000),
                            data=[KeyStringValuePair(key=item.key, value=item.val) for item in log.items],
                        ) for log in span.logs],
                        tags=[KeyStringValuePair(
                            key=tag.key,
                            value=tag.val,
                        ) for tag in span.iter_tags()],
                        refs=[SegmentReference(
                            refType=0 if ref.ref_type == 'CrossProcess' else 1,
                            traceId=ref.trace_id,
                            parentTraceSegmentId=ref.segment_id,
                            parentSpanId=ref.span_id,
                            parentService=ref.service,
                            parentServiceInstance=ref.service_instance,
                            parentEndpoint=ref.endpoint,
                            networkAddressUsedAtPeer=ref.client_address,
                        ) for ref in span.refs if ref.trace_id],
                    ) for span in segment.spans],
                )

                yield s

        try:
            await self.traces_reporter.report(generator())
        except grpc.aio.AioRpcError:
            self.on_error()
            raise  # reraise so that incremental reconnect wait can process

    async def report_log(self, queue: Queue):
        async def generator():
            while True:
                # Let eventloop schedule blocking instead of user configuration: `config.agent_queue_timeout`
                log_data = await queue.get()  # type: LogData

                queue.task_done()

                if logger_debug_enabled:
                    logger.debug('Reporting Log %s', log_data.timestamp)

                yield log_data

        try:
            await self.log_reporter.report(generator())
        except grpc.aio.AioRpcError:
            self.on_error()
            raise

    async def report_meter(self, queue: Queue):
        async def generator():
            while True:
                # Let eventloop schedule blocking instead of user configuration: `config.agent_queue_timeout`
                meter_data = await queue.get()  # type: MeterData

                queue.task_done()

                if logger_debug_enabled:
                    logger.debug('Reporting Meter %s', meter_data.timestamp)

                yield meter_data

        try:
            await self.meter_reporter.report(generator())
        except grpc.aio.AioRpcError:
            self.on_error()
            raise

    async def report_snapshot(self, queue: Queue):
        async def generator():
            while True:
                # Let eventloop schedule blocking instead of user configuration: `config.agent_queue_timeout`
                snapshot = await queue.get()  # type: TracingThreadSnapshot

                queue.task_done()

                transform_snapshot = ThreadSnapshot(
                    taskId=str(snapshot.task_id),
                    traceSegmentId=str(snapshot.trace_segment_id),
                    time=int(snapshot.time),
                    sequence=int(snapshot.sequence),
                    stack=ThreadStack(codeSignatures=snapshot.stack_list)
                )

                yield transform_snapshot

        try:
            await self.profile_channel.report(generator())
        except grpc.aio.AioRpcError:
            self.on_error()
            raise
