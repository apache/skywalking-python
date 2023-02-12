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

import grpc

from skywalking import config
from skywalking.client import ServiceManagementClient, TraceSegmentReportService, ProfileTaskChannelService, \
    LogDataReportService, MeterReportService
from skywalking.command import command_service
from skywalking.loggings import logger, logger_debug_enabled
from skywalking.profile import profile_task_execution_service
from skywalking.profile.profile_task import ProfileTask
from skywalking.protocol.language_agent.Tracing_pb2_grpc import TraceSegmentReportServiceStub
from skywalking.protocol.logging.Logging_pb2_grpc import LogReportServiceStub
from skywalking.protocol.management.Management_pb2 import InstancePingPkg, InstanceProperties
from skywalking.protocol.language_agent.Meter_pb2_grpc import MeterReportServiceStub
from skywalking.protocol.management.Management_pb2_grpc import ManagementServiceStub
from skywalking.protocol.profile.Profile_pb2 import ProfileTaskCommandQuery, ProfileTaskFinishReport
from skywalking.protocol.profile.Profile_pb2_grpc import ProfileTaskStub


class GrpcServiceManagementClient(ServiceManagementClient):
    def __init__(self, channel: grpc.Channel):
        super().__init__()
        self.instance_properties = self.get_instance_properties_proto()
        self.service_stub = ManagementServiceStub(channel)

    def send_instance_props(self):
        self.service_stub.reportInstanceProperties(InstanceProperties(
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
            properties=self.instance_properties,
        ))

    def send_heart_beat(self):
        self.refresh_instance_props()

        self.service_stub.keepAlive(InstancePingPkg(
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
        ))

        if logger_debug_enabled:
            logger.debug(
                'service heart beats, [%s], [%s]',
                config.agent_name,
                config.agent_instance_name,
            )


class GrpcTraceSegmentReportService(TraceSegmentReportService):
    def __init__(self, channel: grpc.Channel):
        self.report_stub = TraceSegmentReportServiceStub(channel)

    def report(self, generator):
        self.report_stub.collect(generator)


class GrpcMeterReportService(MeterReportService):
    def __init__(self, channel: grpc.Channel):
        self.report_stub = MeterReportServiceStub(channel)

    def report_batch(self, generator):
        self.report_stub.collectBatch(generator)

    def report(self, generator):
        self.report_stub.collect(generator)


class GrpcLogDataReportService(LogDataReportService):
    def __init__(self, channel: grpc.Channel):
        self.report_stub = LogReportServiceStub(channel)

    def report(self, generator):
        self.report_stub.collect(generator)


class GrpcProfileTaskChannelService(ProfileTaskChannelService):
    def __init__(self, channel: grpc.Channel):
        self.profile_stub = ProfileTaskStub(channel)

    def do_query(self):
        query = ProfileTaskCommandQuery(
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
            lastCommandTime=profile_task_execution_service.get_last_command_create_time()
        )

        commands = self.profile_stub.getProfileTaskCommands(query)
        command_service.receive_command(commands)

    def report(self, generator):
        self.profile_stub.collectSnapshot(generator)

    def finish(self, task: ProfileTask):
        finish_report = ProfileTaskFinishReport(
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
            taskId=task.task_id
        )
        self.profile_stub.reportTaskFinish(finish_report)
