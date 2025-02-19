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
from asyncio import Queue

from skywalking import config
from skywalking.agent import ProtocolAsync
from skywalking.client.kafka_aio import KafkaServiceManagementClientAsync, KafkaTraceSegmentReportServiceAsync, \
    KafkaLogDataReportServiceAsync, KafkaMeterDataReportServiceAsync
from skywalking.loggings import logger, getLogger, logger_debug_enabled
from skywalking.protocol.common.Common_pb2 import KeyStringValuePair
from skywalking.protocol.language_agent.Tracing_pb2 import SegmentObject, SpanObject, Log, SegmentReference
from skywalking.protocol.language_agent.Meter_pb2 import MeterData
from skywalking.protocol.logging.Logging_pb2 import LogData
from skywalking.trace.segment import Segment

# avoid too many kafka logs
logger_kafka = getLogger('kafka')
logger_kafka.setLevel(max(logging.WARN, logger.level))


class KafkaProtocolAsync(ProtocolAsync):
    def __init__(self):
        self.service_management = KafkaServiceManagementClientAsync()
        self.traces_reporter = KafkaTraceSegmentReportServiceAsync()
        self.log_reporter = KafkaLogDataReportServiceAsync()
        self.meter_reporter = KafkaMeterDataReportServiceAsync()

    async def heartbeat(self):
        await self.service_management.send_heart_beat()

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
        except Exception as e:
            if logger_debug_enabled:
                logger.debug('reporting segment failed: %s', e)

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
            await self.log_reporter.report(generator=generator())
        except Exception as e:
            if logger_debug_enabled:
                logger.debug('reporting log failed: %s', e)

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
            await self.meter_reporter.report(generator=generator())
        except Exception as e:
            if logger_debug_enabled:
                logger.debug('reporting meter failed: %s', e)

    # TODO: implement profiling for kafka
    async def report_snapshot(self, queue: Queue):
        ...

    async def query_profile_commands(self):
        ...

    async def notify_profile_task_finish(self, task):
        ...
