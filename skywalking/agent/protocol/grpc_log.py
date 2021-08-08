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
from skywalking.agent.protocol.interceptors import header_adder_interceptor
from skywalking.client.grpc import GrpcServiceManagementClient, GrpcLogDataReportService
from skywalking.loggings import logger
from skywalking.protocol.logging.Logging_pb2 import LogData


class GrpcLogProtocol(Protocol):
    def __init__(self):
        self.properties_sent = False
        self.state = None

        if config.force_tls:
            self.channel = grpc.secure_channel(config.log_grpc_collector_address, grpc.ssl_channel_credentials(),
                                               options=(('grpc.max_send_message_length',
                                                         config.log_grpc_reporter_max_message_size),))
        else:
            self.channel = grpc.insecure_channel(config.log_grpc_collector_address,
                                                 options=(('grpc.max_send_message_length',
                                                           config.log_grpc_reporter_max_message_size),))
        if config.authentication:
            self.channel = grpc.intercept_channel(
                self.channel, header_adder_interceptor('authentication', config.authentication)
            )

        self.channel.subscribe(self._cb, try_to_connect=True)
        self.service_management = GrpcServiceManagementClient(self.channel)
        self.log_reporter = GrpcLogDataReportService(self.channel)

    def _cb(self, state):
        logger.debug('grpc log reporter channel connectivity changed, [%s -> %s]', self.state, state)
        self.state = state

    def heartbeat(self):
        try:
            if not self.properties_sent:
                self.service_management.send_instance_props()
                self.properties_sent = True

            logger.debug(
                'log reporter service heart beats, [%s], [%s]',
                config.service_name,
                config.service_instance,
            )
            self.service_management.send_heart_beat()

        except grpc.RpcError:
            self.on_error()

    def on_error(self):
        traceback.print_exc() if logger.isEnabledFor(logging.DEBUG) else None
        self.channel.unsubscribe(self._cb)
        self.channel.subscribe(self._cb, try_to_connect=True)

    def report(self, queue: Queue, block: bool = True):
        start = time()

        def generator():
            while True:
                try:
                    timeout = config.QUEUE_TIMEOUT - int(time() - start)  # type: int
                    if timeout <= 0:  # this is to make sure we exit eventually instead of being fed continuously
                        return
                    log_data = queue.get(block=block, timeout=timeout)  # type: LogData
                except Empty:
                    return

                queue.task_done()

                logger.debug('Reporting Log')

                yield log_data

        try:
            self.log_reporter.report(generator())

        except grpc.RpcError:
            self.on_error()
