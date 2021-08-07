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

import atexit
import os
from queue import Queue, Full
from threading import Thread, Event
from typing import TYPE_CHECKING

from skywalking import config, plugins
from skywalking import loggings
from skywalking.agent.protocol import Protocol
from skywalking.agent.protocol.grpc_log import GrpcLogProtocol
from skywalking.command import command_service
from skywalking.config import profile_active, profile_task_query_interval
from skywalking.loggings import logger
from skywalking.protocol.logging.Logging_pb2 import LogData

if TYPE_CHECKING:
    from skywalking.trace.context import Segment

__started = False
__protocol = __log_protocol = Protocol()  # type: Protocol
__heartbeat_thread = __report_thread = __log_report_thread = __query_profile_thread = __command_dispatch_thread \
    = __queue = __log_queue = __finished = None


def __heartbeat():
    while not __finished.is_set():
        try:
            __protocol.heartbeat()
        except Exception as exc:
            logger.error(str(exc))

        __finished.wait(30)


def __report():
    while not __finished.is_set():
        try:
            __protocol.report(__queue)  # is blocking actually, blocks for max config.QUEUE_TIMEOUT seconds
        except Exception as exc:
            logger.error(str(exc))

        __finished.wait(0)


def __log_heartbeat():
    while not __finished.is_set():
        if log_connected():
            __log_protocol.heartbeat()

        __finished.wait(30 if log_connected() else 3)


def __log_report():
    while not __finished.is_set():
        if log_connected():
            __log_protocol.report(__log_queue)

        __finished.wait(1)


def __query_profile_command():
    while not __finished.is_set():
        try:
            __protocol.query_profile_commands()
        except Exception as exc:
            logger.error(str(exc))

        __finished.wait(profile_task_query_interval)


def __command_dispatch():
    # command dispatch will stuck when there are no commands
    command_service.dispatch()


def __init_threading():
    global __heartbeat_thread, __report_thread, __log_report_thread, __query_profile_thread, \
        __command_dispatch_thread, __queue, __log_queue, __finished

    __queue = Queue(maxsize=config.max_buffer_size)
    __finished = Event()
    __heartbeat_thread = Thread(name='HeartbeatThread', target=__heartbeat, daemon=True)
    __report_thread = Thread(name='ReportThread', target=__report, daemon=True)
    __query_profile_thread = Thread(name='QueryProfileCommandThread', target=__query_profile_command, daemon=True)
    __command_dispatch_thread = Thread(name="CommandDispatchThread", target=__command_dispatch, daemon=True)

    __heartbeat_thread.start()
    __report_thread.start()
    __command_dispatch_thread.start()

    if config.log_grpc_reporter_active:
        __log_queue = Queue(maxsize=10000)
        __log_heartbeat_thread = Thread(name='HeartbeatThread', target=__log_heartbeat, daemon=True)
        __log_report_thread = Thread(name='LogReportThread', target=__log_report, daemon=True)
        __log_report_thread.start()
        __log_heartbeat_thread.start()

    if profile_active:
        __query_profile_thread.start()


def __init():
    global __protocol, __log_protocol

    if config.protocol == 'grpc':
        from skywalking.agent.protocol.grpc import GrpcProtocol
        __protocol = GrpcProtocol()
    elif config.protocol == 'http':
        from skywalking.agent.protocol.http import HttpProtocol
        __protocol = HttpProtocol()
    elif config.protocol == "kafka":
        from skywalking.agent.protocol.kafka import KafkaProtocol
        __protocol = KafkaProtocol()

    plugins.install()
    if config.log_grpc_reporter_active:
        from skywalking import log
        __log_protocol = GrpcLogProtocol()
        log.install()
    __init_threading()


def __fini():
    __protocol.report(__queue, False)
    __queue.join()
    if config.log_grpc_reporter_active:
        __log_protocol.report(__log_queue, False)
        __log_queue.join()
    __finished.set()


def __fork_before():
    if config.protocol != 'http':
        logger.warning('fork() not currently supported with %s protocol' % config.protocol)

    # TODO: handle __queue and __finished correctly (locks, mutexes, etc...), need to lock before fork and unlock after
    # if possible, or ensure they are not locked in threads (end threads and restart after fork?)

    __protocol.fork_before()


def __fork_after_in_parent():
    __protocol.fork_after_in_parent()


def __fork_after_in_child():
    __protocol.fork_after_in_child()
    __init_threading()


def start():
    global __started
    if __started:
        return
    __started = True

    flag = False
    try:
        from gevent import monkey
        flag = monkey.is_module_patched("socket")
    except ModuleNotFoundError:
        logger.debug("it was found that no gevent was used, if you don't use, please ignore.")
    if flag:
        import grpc.experimental.gevent as grpc_gevent
        grpc_gevent.init_gevent()

    loggings.init()
    config.finalize()

    __init()

    atexit.register(__fini)

    if (hasattr(os, 'register_at_fork')):
        os.register_at_fork(before=__fork_before, after_in_parent=__fork_after_in_parent,
                            after_in_child=__fork_after_in_child)


def stop():
    atexit.unregister(__fini)
    __fini()


def started():
    return __started


def isfull():
    return __queue.full()


def log_connected():
    return __log_protocol.connected()


def archive(segment: 'Segment'):
    try:  # unlike checking __queue.full() then inserting, this is atomic
        __queue.put(segment, block=False)
    except Full:
        logger.warning('the queue is full, the segment will be abandoned')


def archive_log(log_data: 'LogData'):
    try:
        __log_queue.put(log_data, block=False)
    except Full:
        logger.warning('the queue is full, the log will be abandoned')
