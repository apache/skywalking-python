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
from skywalking.client import ServiceManagementClientAsync, TraceSegmentReportServiceAsync, \
    ProfileTaskChannelServiceAsync, LogDataReportServiceAsync, MeterReportServiceAsync
from skywalking.command import command_service_async
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


class GrpcServiceManagementClientAsync(ServiceManagementClientAsync):
    def __init__(self, channel: grpc.aio.Channel):
        super().__init__()
        self.instance_properties = self.get_instance_properties_proto()
        self.service_stub = ManagementServiceStub(channel)

    async def send_instance_props(self):
        await self.service_stub.reportInstanceProperties(InstanceProperties(
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
            properties=self.instance_properties,
        ))

    async def send_heart_beat(self):
        await self.refresh_instance_props()

        await self.service_stub.keepAlive(InstancePingPkg(
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
        ))

        if logger_debug_enabled:
            logger.debug(
                'service heart beats, [%s], [%s]',
                config.agent_name,
                config.agent_instance_name,
            )


class GrpcTraceSegmentReportServiceAsync(TraceSegmentReportServiceAsync):
    def __init__(self, channel: grpc.aio.Channel):
        super().__init__()
        self.report_stub = TraceSegmentReportServiceStub(channel)

    async def report(self, generator):
        await self.report_stub.collect(generator)


class GrpcMeterReportServiceAsync(MeterReportServiceAsync):
    def __init__(self, channel: grpc.aio.Channel):
        super().__init__()
        self.report_stub = MeterReportServiceStub(channel)

    async def report_batch(self, generator):
        await self.report_stub.collectBatch(generator)

    async def report(self, generator):
        await self.report_stub.collect(generator)


class GrpcLogReportServiceAsync(LogDataReportServiceAsync):
    def __init__(self, channel: grpc.aio.Channel):
        super().__init__()
        self.report_stub = LogReportServiceStub(channel)

    async def report(self, generator):
        await self.report_stub.collect(generator)


class GrpcProfileTaskChannelServiceAsync(ProfileTaskChannelServiceAsync):
    def __init__(self, channel: grpc.aio.Channel):
        self.profile_stub = ProfileTaskStub(channel)

    async def do_query(self):
        query = ProfileTaskCommandQuery(
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
            lastCommandTime=profile_task_execution_service.get_last_command_create_time()
        )

        commands = await self.profile_stub.getProfileTaskCommands(query)
        command_service_async.receive_command(commands)  # put_nowait() not need to be awaited

    async def report(self, generator):
        await self.profile_stub.collectSnapshot(generator)

    async def finish(self, task: ProfileTask):
        finish_report = ProfileTaskFinishReport(
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
            taskId=task.task_id
        )
        await self.profile_stub.reportTaskFinish(finish_report)
