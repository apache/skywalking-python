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
from threading import Thread, Event
from typing import TYPE_CHECKING

from skywalking import config, plugins
from skywalking.agent.protocol import Protocol

if TYPE_CHECKING:
    from skywalking.trace.context import Segment

logger = logging.getLogger(__name__)


def __heartbeat():
    while not __finished.is_set():
        if connected():
            __protocol.heartbeat()

        __finished.wait(30 if connected() else 3)


def __report():
    while not __finished.is_set():
        if connected():
            __protocol.report(__queue)
            break
        else:
            __finished.wait(1)


__heartbeat_thread = Thread(name='HeartbeatThread', target=__heartbeat, daemon=True)
__report_thread = Thread(name='ReportThread', target=__report, daemon=True)
__queue = Queue(maxsize=10000)
__finished = Event()
__protocol = Protocol()  # type: Protocol
__started = False


def __init():
    global __protocol
    if config.protocol == 'grpc':
        from skywalking.agent.protocol.grpc import GrpcProtocol
        __protocol = GrpcProtocol()
    elif config.protocol == 'http':
        from skywalking.agent.protocol.http import HttpProtocol
        __protocol = HttpProtocol()

    plugins.install()


def start():
    global __started
    if __started:
        raise RuntimeError('the agent can only be started once')
    from skywalking import loggings
    loggings.init()
    __started = True
    __init()
    __heartbeat_thread.start()
    __report_thread.start()


def stop():
    __finished.set()


def connected():
    return __protocol.connected()


def archive(segment: 'Segment'):
    if __queue.full():
        logger.warning('the queue is full, the segment will be abandoned')
        return

    __queue.put(segment)
