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

from asyncio import Queue, Event

from skywalking.agent import ProtocolAsync
from skywalking.client.http_aio import HttpServiceManagementClientAsync, HttpTraceSegmentReportServiceAsync, \
    HttpLogDataReportServiceAsync
from skywalking.loggings import logger, logger_debug_enabled
from skywalking.protocol.logging.Logging_pb2 import LogData
from skywalking.trace.segment import Segment


class HttpProtocolAsync(ProtocolAsync):
    def __init__(self):
        self.properties_sent = Event()
        self.service_management = HttpServiceManagementClientAsync()
        self.traces_reporter = HttpTraceSegmentReportServiceAsync()
        self.log_reporter = HttpLogDataReportServiceAsync()

    async def heartbeat(self):
        if not self.properties_sent.is_set():
            logger.debug('Sending instance properties')
            await self.service_management.send_instance_props()
            self.properties_sent.set()

        logger.debug('Sending heartbeat')
        await self.service_management.send_heart_beat()
        logger.debug('Heartbeat sent')

    async def report_segment(self, queue: Queue):
        async def generator():
            while True:
                # Let eventloop schedule blocking instead of user configuration: `config.agent_queue_timeout`
                segment = await queue.get()  # type: Segment

                queue.task_done()

                if logger_debug_enabled:
                    logger.debug('reporting segment %s', segment)

                yield segment

        try:
            await self.traces_reporter.report(generator=generator())
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

    # meter support requires OAP side HTTP handler to be implemented
    async def report_meter(self, queue: Queue):
        ...

    async def report_snapshot(self, queue: Queue):
        ...

    async def query_profile_commands(self):
        ...

    async def notify_profile_task_finish(self, task):
        ...
