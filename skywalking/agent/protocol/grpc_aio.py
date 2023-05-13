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


class GrpcProtocolAsync(Protocol):
    """
    grpc for asyncio
    """
    def __init__(self):
        self.properties_sent = False

        # grpc.aio.channel do not have subscribe() method to set a callback when channel state changed
        # instead, it has a get_state() method to get the current state of the channel
        # consider the channel state is only used for debug, the cost of monitoring this value is too high.
        # self.state = None

        interceptors = [header_adder_interceptor_async('authentication', config.agent_authentication)] \
                if config.agent_authentication else None

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
    
    def query_profile_commands(self):
        ...

    def notify_profile_task_finish(self, task: ProfileTask):
        ...

    async def heartbeat(self):
        try:
            if not self.properties_sent:
                await self.service_management.send_instance_props()
                self.properties_sent = True

            await self.service_management.send_heart_beat()

        except grpc.RpcError:
            self.on_error()
            raise

    def on_error(self):
        traceback.print_exc() if logger.isEnabledFor(logging.DEBUG) else None
