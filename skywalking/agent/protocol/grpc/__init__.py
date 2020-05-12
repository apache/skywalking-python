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
from queue import Queue

import grpc

from common.Common_pb2 import KeyStringValuePair
from language_agent.Tracing_pb2 import SegmentObject, SpanObject, Log, SegmentReference
from skywalking import config
from skywalking.agent import Protocol
from skywalking.agent.protocol.grpc.interceptors import header_adder_interceptor
from skywalking.client.grpc import GrpcServiceManagementClient, GrpcTraceSegmentReportService
from skywalking.trace.segment import Segment

logger = logging.getLogger(__name__)


class GrpcProtocol(Protocol):
    def __init__(self):
        self.state = None
        self.channel = grpc.insecure_channel(config.collector_address)
        if config.authentication:
            self.channel = grpc.intercept_channel(
                self.channel, header_adder_interceptor('authentication', config.authentication)
            )

        def cb(state):
            logger.debug('grpc channel connectivity changed, [%s -> %s]', self.state, state)
            self.state = state
            if self.connected():
                self.service_management.send_instance_props()

        self.channel.subscribe(cb, try_to_connect=True)
        self.service_management = GrpcServiceManagementClient(self.channel)
        self.traces_reporter = GrpcTraceSegmentReportService(self.channel)

    def heartbeat(self):
        self.service_management.send_heart_beat()

    def connected(self):
        return self.state == grpc.ChannelConnectivity.READY

    def report(self, queue: Queue):
        def generator():
            while True:
                segment = queue.get()  # type: Segment

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
                            refType=0,
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

        self.traces_reporter.report(generator())
