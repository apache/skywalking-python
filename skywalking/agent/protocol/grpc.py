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
from queue import Queue, Empty
from time import time

import grpc

from skywalking import config
from skywalking.agent import Protocol
from skywalking.agent.protocol.interceptors import header_adder_interceptor
from skywalking.client.grpc import GrpcServiceManagementClient, GrpcTraceSegmentReportService, \
    GrpcProfileTaskChannelService, GrpcLogDataReportService
from skywalking.loggings import logger, logger_debug_enabled
from skywalking.profile.profile_task import ProfileTask
from skywalking.profile.snapshot import TracingThreadSnapshot
from skywalking.protocol.common.Common_pb2 import KeyStringValuePair
from skywalking.protocol.language_agent.Tracing_pb2 import SegmentObject, SpanObject, Log, SegmentReference
from skywalking.protocol.logging.Logging_pb2 import LogData
from skywalking.protocol.profile.Profile_pb2 import ThreadSnapshot, ThreadStack
from skywalking.trace.segment import Segment


class GrpcProtocol(Protocol):
    def __init__(self):
        self.properties_sent = False
        self.state = None

        if config.force_tls:
            self.channel = grpc.secure_channel(config.collector_address, grpc.ssl_channel_credentials())
        else:
            self.channel = grpc.insecure_channel(config.collector_address)

        if config.authentication:
            self.channel = grpc.intercept_channel(
                self.channel, header_adder_interceptor('authentication', config.authentication)
            )

        self.channel.subscribe(self._cb, try_to_connect=True)
        self.service_management = GrpcServiceManagementClient(self.channel)
        self.traces_reporter = GrpcTraceSegmentReportService(self.channel)
        self.profile_channel = GrpcProfileTaskChannelService(self.channel)
        self.log_reporter = GrpcLogDataReportService(self.channel)

    def _cb(self, state):
        if logger_debug_enabled:
            logger.debug('grpc channel connectivity changed, [%s -> %s]', self.state, state)
        self.state = state

    def query_profile_commands(self):
        if logger_debug_enabled:
            logger.debug('query profile commands')
        self.profile_channel.do_query()

    def notify_profile_task_finish(self, task: ProfileTask):
        self.profile_channel.finish(task)

    def heartbeat(self):
        try:
            if not self.properties_sent:
                self.service_management.send_instance_props()
                self.properties_sent = True

            self.service_management.send_heart_beat()

        except grpc.RpcError:
            self.on_error()
            raise

    def on_error(self):
        traceback.print_exc() if logger.isEnabledFor(logging.DEBUG) else None
        self.channel.unsubscribe(self._cb)
        self.channel.subscribe(self._cb, try_to_connect=True)

    def report(self, queue: Queue, block: bool = True):
        start = None

        def generator():
            nonlocal start

            while True:
                try:
                    timeout = config.QUEUE_TIMEOUT  # type: int
                    if not start:  # make sure first time through queue is always checked
                        start = time()
                    else:
                        timeout -= int(time() - start)
                        if timeout <= 0:  # this is to make sure we exit eventually instead of being fed continuously
                            return
                    segment = queue.get(block=block, timeout=timeout)  # type: Segment
                except Empty:
                    return

                queue.task_done()

                if logger_debug_enabled:
                    logger.debug('reporting segment %s', segment)

                s = SegmentObject(
                    traceId=str(segment.related_traces[0]),
                    traceSegmentId=str(segment.segment_id),
                    service=config.service_name,
                    serviceInstance=config.service_instance,
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
                            value=str(tag.val),
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
            self.traces_reporter.report(generator())
        except grpc.RpcError:
            self.on_error()
            raise  # reraise so that incremental reconnect wait can process

    def report_log(self, queue: Queue, block: bool = True):
        start = None

        def generator():
            nonlocal start

            while True:
                try:
                    timeout = config.QUEUE_TIMEOUT  # type: int
                    if not start:  # make sure first time through queue is always checked
                        start = time()
                    else:
                        timeout -= int(time() - start)
                        if timeout <= 0:  # this is to make sure we exit eventually instead of being fed continuously
                            return
                    log_data = queue.get(block=block, timeout=timeout)  # type: LogData
                except Empty:
                    return

                queue.task_done()

                if logger_debug_enabled:
                    logger.debug('Reporting Log')

                yield log_data

        try:
            self.log_reporter.report(generator())
        except grpc.RpcError:
            self.on_error()
            raise

    def send_snapshot(self, queue: Queue, block: bool = True):
        start = None

        def generator():
            nonlocal start

            while True:
                try:
                    timeout = config.QUEUE_TIMEOUT  # type: int
                    if not start:  # make sure first time through queue is always checked
                        start = time()
                    else:
                        timeout -= int(time() - start)
                        if timeout <= 0:  # this is to make sure we exit eventually instead of being fed continuously
                            return
                    snapshot = queue.get(block=block, timeout=timeout)  # type: TracingThreadSnapshot
                except Empty:
                    return

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
            self.profile_channel.send(generator())
        except grpc.RpcError:
            self.on_error()
            raise
