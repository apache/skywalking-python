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

from queue import Queue, Empty
from time import time

from skywalking import config
from skywalking.agent import Protocol
from skywalking.client.http import HttpServiceManagementClient, HttpTraceSegmentReportService, HttpLogDataReportService
from skywalking.loggings import logger, logger_debug_enabled
from skywalking.protocol.logging.Logging_pb2 import LogData
from skywalking.trace.segment import Segment


class HttpProtocol(Protocol):
    def __init__(self):
        self.properties_sent = False
        self.service_management = HttpServiceManagementClient()
        self.traces_reporter = HttpTraceSegmentReportService()
        self.log_reporter = HttpLogDataReportService()

    def fork_after_in_child(self):
        self.service_management.fork_after_in_child()
        self.traces_reporter.fork_after_in_child()

    def heartbeat(self):
        if not self.properties_sent:
            self.service_management.send_instance_props()
            self.properties_sent = True
        self.service_management.send_heart_beat()

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

                yield segment

        try:
            self.traces_reporter.report(generator=generator())
        except Exception:
            pass

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
            self.log_reporter.report(generator=generator())
        except Exception:
            pass
