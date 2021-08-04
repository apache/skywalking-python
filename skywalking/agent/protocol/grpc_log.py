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
from queue import Queue, Empty, Full
from time import time

import grpc

from skywalking import config
from skywalking.agent import Protocol
from skywalking.agent.protocol.interceptors import header_adder_interceptor
from skywalking.client.grpc import GrpcServiceManagementClient, GrpcLogDataReportService
from skywalking.loggings import logger
from skywalking.protocol.logging.Logging_pb2 import LogData


class GrpcLogProtocol(Protocol):
    def __init__(self):
        self.state = None

        if config.force_tls:
            self.channel = grpc.secure_channel(config.log_grpc_collector_address, grpc.ssl_channel_credentials(),
                                               options=[
                                                   ('grpc.max_connection_age_grace_ms',
                                                    1000 * config.log_grpc_reporter_upstream_timeout),
                                                   ('grpc.max_send_message_length',
                                                    config.log_grpc_reporter_max_message_size)
                                               ])
        else:
            self.channel = grpc.insecure_channel(config.collector_address,
                                                 options=(('grpc.max_connection_age_grace_ms',
                                                           1000 * config.log_grpc_reporter_upstream_timeout),))

        if config.authentication:
            self.channel = grpc.intercept_channel(
                self.channel, header_adder_interceptor('authentication', config.authentication)
            )

        self.channel.subscribe(self._cb, try_to_connect=True)
        self.service_management = GrpcServiceManagementClient(self.channel)
        self.log_reporter = GrpcLogDataReportService(self.channel)

    def _cb(self, state):
        logger.debug('grpc log channel connectivity changed, [%s -> %s]', self.state, state)
        self.state = state
        if self.connected():
            try:
                self.service_management.send_instance_props()
            except grpc.RpcError:
                self.on_error()

    def heartbeat(self):
        try:
            logger.debug(
                'log reporter service heart beats, [%s], [%s]',
                config.service_name,
                config.service_instance,
            )
            self.service_management.send_heart_beat()
        except grpc.RpcError:
            self.on_error()

    def connected(self):
        return self.state == grpc.ChannelConnectivity.READY

    def on_error(self):
        traceback.print_exc() if logger.isEnabledFor(logging.DEBUG) else None
        self.channel.unsubscribe(self._cb)
        self.channel.subscribe(self._cb, try_to_connect=True)

    def report(self, queue: Queue, block: bool = True):
        start = time()
        log_data = None

        def generator():
            nonlocal log_data

            while True:
                try:
                    timeout = max(0, config.QUEUE_TIMEOUT - int(time() - start))  # type: int
                    log_data = queue.get(block=block, timeout=timeout)  # type: LogData
                except Empty:
                    return

                logger.debug('Reporting Log %s', log_data)

                yield log_data
                queue.task_done()

        try:
            self.log_reporter.report(generator())

        except grpc.RpcError:
            self.on_error()

            if log_data:
                try:
                    queue.put(log_data, block=False)
                except Full:
                    pass
