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
from skywalking.loggings import logger
import traceback
from queue import Queue, Empty, Full
from time import time

import grpc

from skywalking import config
from skywalking.agent import Protocol
from skywalking.agent.protocol.interceptors import header_adder_interceptor
from skywalking.client.grpc import GrpcServiceManagementClient, GrpcTraceSegmentReportService
from skywalking.protocol.common.Common_pb2 import KeyStringValuePair
from skywalking.protocol.language_agent.Tracing_pb2 import SegmentObject, SpanObject, Log, SegmentReference
from skywalking.trace.segment import Segment


class GrpcProtocol(Protocol):
    def __init__(self):
        self.state = None
        self.channel = grpc.insecure_channel(config.collector_address)
        if config.authentication:
            self.channel = grpc.intercept_channel(
                self.channel, header_adder_interceptor('authentication', config.authentication)
            )

        self.channel.subscribe(self._cb, try_to_connect=True)
        self.service_management = GrpcServiceManagementClient(self.channel)
        self.traces_reporter = GrpcTraceSegmentReportService(self.channel)

    def _cb(self, state):
        logger.debug('grpc channel connectivity changed, [%s -> %s]', self.state, state)
        self.state = state
        if self.connected():
            try:
                self.service_management.send_instance_props()
            except grpc.RpcError:
                self.on_error()

    def heartbeat(self):
        try:
            self.service_management.send_heart_beat()
        except grpc.RpcError:
            self.on_error()

    def connected(self):
        return self.state == grpc.ChannelConnectivity.READY

    def on_error(self):
        traceback.print_exc() if logger.isEnabledFor(logging.DEBUG) else None
        self.channel.unsubscribe(self._cb)
        self.channel.subscribe(self._cb, try_to_connect=True)

    def report(self, queue: Queue, block: bool = True):
        start = time()
        segment = None

        def generator():
            nonlocal segment

            while True:
                try:
                    timeout = max(0, config.QUEUE_TIMEOUT - int(time() - start))  # type: int
                    segment = queue.get(block=block, timeout=timeout)  # type: Segment
                except Empty:
                    return

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
                            key=str(tag.key),
                            value=str(tag.val),
                        ) for tag in span.tags],
                        refs=[SegmentReference(
                            refType=0 if ref.ref_type == "CrossProcess" else 1,
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

                queue.task_done()

        try:
            self.traces_reporter.report(generator())

        except grpc.RpcError:
            self.on_error()

            if segment:
                try:
                    queue.put(segment, block=False)
                except Full:
                    pass
