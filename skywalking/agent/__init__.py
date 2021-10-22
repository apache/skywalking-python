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

from skywalking.protocol.logging.Logging_pb2 import LogData

from skywalking import config, plugins
from skywalking import loggings
from skywalking import profile
from skywalking.agent.protocol import Protocol
from skywalking.command import command_service
from skywalking.loggings import logger
from skywalking.profile.profile_task import ProfileTask
from skywalking.profile.snapshot import TracingThreadSnapshot

if TYPE_CHECKING:
    from skywalking.trace.context import Segment

__started = False
__protocol = Protocol()  # type: Protocol
__heartbeat_thread = __report_thread = __log_report_thread = __query_profile_thread = __command_dispatch_thread \
    = __send_profile_thread = __queue = __log_queue = __snapshot_queue = __finished = None


def __heartbeat():
    wait = base = 30

    while not __finished.is_set():
        try:
            __protocol.heartbeat()
            wait = base  # reset to base wait time on success
        except Exception as exc:
            logger.error(str(exc))
            wait = min(60, wait * 2 or 1)  # double wait time with each consecutive error up to a maximum

        __finished.wait(wait)


def __report():
    wait = base = 0

    while not __finished.is_set():
        try:
            __protocol.report(__queue)  # is blocking actually, blocks for max config.QUEUE_TIMEOUT seconds
            wait = base
        except Exception as exc:
            logger.error(str(exc))
            wait = min(60, wait * 2 or 1)

        __finished.wait(wait)


def __report_log():
    wait = base = 0

    while not __finished.is_set():
        try:
            __protocol.report_log(__log_queue)
            wait = base
        except Exception as exc:
            logger.error(str(exc))
            wait = min(60, wait * 2 or 1)

        __finished.wait(wait)


def __send_profile_snapshot():
    wait = base = 0.5

    while not __finished.is_set():
        try:
            __protocol.send_snapshot(__snapshot_queue)
            wait = base
        except Exception as exc:
            logger.error(str(exc))
            wait = min(60, wait * 2 or 1)

        __finished.wait(wait)


def __query_profile_command():
    wait = base = config.get_profile_task_interval

    while not __finished.is_set():
        try:
            __protocol.query_profile_commands()
            wait = base
        except Exception as exc:
            logger.error(str(exc))
            wait = min(60, wait * 2 or 1)

        __finished.wait(wait)


def __command_dispatch():
    # command dispatch will stuck when there are no commands
    command_service.dispatch()


def __init_threading():
    global __heartbeat_thread, __report_thread, __log_report_thread, __query_profile_thread, \
        __command_dispatch_thread, __send_profile_thread, __queue, __log_queue, __snapshot_queue, __finished

    __queue = Queue(maxsize=config.max_buffer_size)
    __finished = Event()
    __heartbeat_thread = Thread(name='HeartbeatThread', target=__heartbeat, daemon=True)
    __report_thread = Thread(name='ReportThread', target=__report, daemon=True)
    __command_dispatch_thread = Thread(name='CommandDispatchThread', target=__command_dispatch, daemon=True)

    __heartbeat_thread.start()
    __report_thread.start()
    __command_dispatch_thread.start()

    if config.log_reporter_active:
        __log_queue = Queue(maxsize=config.log_reporter_max_buffer_size)
        __log_report_thread = Thread(name='LogReportThread', target=__report_log, daemon=True)
        __log_report_thread.start()

    if config.profile_active:
        __snapshot_queue = Queue(maxsize=config.profile_snapshot_transport_buffer_size)

        __query_profile_thread = Thread(name='QueryProfileCommandThread', target=__query_profile_command, daemon=True)
        __query_profile_thread.start()

        __send_profile_thread = Thread(name='SendProfileSnapShotThread', target=__send_profile_snapshot, daemon=True)
        __send_profile_thread.start()


def __init():
    global __protocol
    if config.protocol == 'grpc':
        from skywalking.agent.protocol.grpc import GrpcProtocol
        __protocol = GrpcProtocol()
    elif config.protocol == 'http':
        from skywalking.agent.protocol.http import HttpProtocol
        __protocol = HttpProtocol()
    elif config.protocol == 'kafka':
        from skywalking.agent.protocol.kafka import KafkaProtocol
        __protocol = KafkaProtocol()

    plugins.install()
    if config.log_reporter_active:  # todo - Add support for printing traceID/ context in logs
        from skywalking import log
        log.install()

    __init_threading()


def __fini():
    __protocol.report(__queue, False)
    __queue.join()

    if config.log_reporter_active:
        __protocol.report_log(__log_queue, False)
        __log_queue.join()

    if config.profile_active:
        __protocol.send_snapshot(__snapshot_queue, False)
        __snapshot_queue.join()

    __finished.set()


def __fork_before():
    if config.protocol != 'http':
        logger.warning(f'fork() not currently supported with {config.protocol} protocol')

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
        flag = monkey.is_module_patched('socket')
    except ModuleNotFoundError:
        logger.debug("it was found that no gevent was used, if you don't use, please ignore.")
    if flag:
        import grpc.experimental.gevent as grpc_gevent
        grpc_gevent.init_gevent()

    loggings.init()
    config.finalize()
    profile.init()

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


def add_profiling_snapshot(snapshot: TracingThreadSnapshot):
    try:
        __snapshot_queue.put(snapshot)
    except Full:
        logger.warning('the snapshot queue is full, the snapshot will be abandoned')


def notify_profile_finish(task: ProfileTask):
    try:
        __protocol.notify_profile_task_finish(task)
    except Exception as e:
        logger.error(f'notify profile task finish to backend fail. {str(e)}')
