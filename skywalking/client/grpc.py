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

import grpc
from common.Common_pb2 import KeyStringValuePair
from language_agent.Tracing_pb2_grpc import TraceSegmentReportServiceStub
from management.Management_pb2 import InstancePingPkg, InstanceProperties
from management.Management_pb2_grpc import ManagementServiceStub

from skywalking import config
from skywalking.client import ServiceManagementClient, TraceSegmentReportService

logger = logging.getLogger(__name__)


class GrpcServiceManagementClient(ServiceManagementClient):
    def __init__(self, channel: grpc.Channel):
        self.service_stub = ManagementServiceStub(channel)

    def send_instance_props(self):
        self.service_stub.reportInstanceProperties(InstanceProperties(
            service=config.service_name,
            serviceInstance=config.service_instance,
            properties=[KeyStringValuePair(key='language', value='Python')],
        ))

    def send_heart_beat(self):
        logger.debug(
            'service heart beats, [%s], [%s]',
            config.service_name,
            config.service_instance,
        )
        self.service_stub.keepAlive(InstancePingPkg(
            service=config.service_name,
            serviceInstance=config.service_instance,
        ))


class GrpcTraceSegmentReportService(TraceSegmentReportService):
    def __init__(self, channel: grpc.Channel):
        self.report_stub = TraceSegmentReportServiceStub(channel)

    def report(self, generator):
        self.report_stub.collect(generator)
