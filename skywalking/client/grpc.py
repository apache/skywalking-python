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

import grpc

from typing import List
from queue import Queue

from skywalking import config
from skywalking.client import ServiceManagementClient, TraceSegmentReportService, ProfileTaskChannelService
from skywalking.protocol.common.Common_pb2 import KeyStringValuePair
from skywalking.protocol.language_agent.Tracing_pb2_grpc import TraceSegmentReportServiceStub
from skywalking.protocol.profile.Profile_pb2_grpc import ProfileTaskStub
from skywalking.protocol.profile.Profile_pb2 import ProfileTaskCommandQuery, ProfileTaskFinishReport
from skywalking.protocol.management.Management_pb2 import InstancePingPkg, InstanceProperties
from skywalking.protocol.management.Management_pb2_grpc import ManagementServiceStub

from skywalking.command import command_service
from skywalking.profile import profile_task_execution_service
from skywalking.profile.profile_task import ProfileTask


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
        self.report_stub.collect(generator, timeout=config.GRPC_TIMEOUT)


class GrpcProfileTaskChannelService(ProfileTaskChannelService):
    def __init__(self, channel: grpc.Channel):
        self.profile_stub = ProfileTaskStub(channel)

    def do_query(self):

        query = ProfileTaskCommandQuery(
            service=config.service_name,
            serviceInstance=config.service_instance,
            lastCommandTime=profile_task_execution_service.get_last_command_create_time()
        )

        commands = self.profile_stub.getProfileTaskCommands(query)
        command_service.receive_command(commands)

    def send(self, generator):
        self.profile_stub.collectSnapshot(generator, timeout=config.GRPC_TIMEOUT)

    def finish(self, task: ProfileTask):
        finish_report = ProfileTaskFinishReport(
            service=config.service_name,
            serviceInstance=config.service_instance,
            taskId=task.task_id
        )
        self.profile_stub.reportTaskFinish(finish_report)

