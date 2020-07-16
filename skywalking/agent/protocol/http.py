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

from skywalking.agent import Protocol
from skywalking.client.http import HttpServiceManagementClient, HttpTraceSegmentReportService
from skywalking.trace.segment import Segment

logger = logging.getLogger(__name__)


class HttpProtocol(Protocol):
    def __init__(self):
        self.properties_sent = False
        self.service_management = HttpServiceManagementClient()
        self.traces_reporter = HttpTraceSegmentReportService()

    def heartbeat(self):
        if not self.properties_sent:
            self.service_management.send_instance_props()
            self.properties_sent = True
        self.service_management.send_heart_beat()

    def connected(self):
        return True

    def report(self, queue: Queue):
        def generator():
            while True:
                segment = queue.get()  # type: Segment

                logger.debug('reporting segment %s', segment)

                yield segment

                queue.task_done()

        self.traces_reporter.report(generator=generator())
