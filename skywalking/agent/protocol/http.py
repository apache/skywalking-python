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

from skywalking.loggings import logger
from queue import Queue, Empty
from time import time

from skywalking import config
from skywalking.agent import Protocol
from skywalking.client.http import HttpServiceManagementClient, HttpTraceSegmentReportService
from skywalking.trace.segment import Segment


class HttpProtocol(Protocol):
    def __init__(self):
        self.properties_sent = False
        self.service_management = HttpServiceManagementClient()
        self.traces_reporter = HttpTraceSegmentReportService()

    def fork_after_in_child(self):
        self.service_management.fork_after_in_child()
        self.traces_reporter.fork_after_in_child()

    def heartbeat(self):
        if not self.properties_sent:
            self.service_management.send_instance_props()
            self.properties_sent = True
        self.service_management.send_heart_beat()

    def report(self, queue: Queue, block: bool = True):
        start = time()

        def generator():
            while True:
                try:
                    timeout = config.QUEUE_TIMEOUT - int(time() - start)  # type: int
                    if timeout <= 0:  # this is to make sure we exit eventually instead of being fed continuously
                        return
                    segment = queue.get(block=block, timeout=timeout)  # type: Segment
                except Empty:
                    return

                queue.task_done()

                logger.debug('reporting segment %s', segment)

                yield segment

        try:
            self.traces_reporter.report(generator=generator())
        except Exception:
            pass
