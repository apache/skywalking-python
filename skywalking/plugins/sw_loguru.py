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
import sys
import traceback
from multiprocessing import current_process
from os.path import basename, splitext
from threading import current_thread

from skywalking import config
from skywalking.agent import agent
from skywalking.protocol.common.Common_pb2 import KeyStringValuePair
from skywalking.protocol.logging.Logging_pb2 import LogData, LogDataBody, TraceContext, LogTags, TextLog
from skywalking.trace.context import get_context
from skywalking.utils.exception import IllegalStateError
from skywalking.utils.filter import sw_filter

link_vector = ['https://pypi.org/project/loguru/']
support_matrix = {
    'loguru': {
        '>=3.7': ['0.6.0']
    }
}
note = """"""


def install():
    from loguru import logger
    from loguru._recattrs import RecordException, RecordFile, RecordLevel, RecordProcess, RecordThread
    from loguru._datetime import aware_now
    from loguru._get_frame import get_frame
    from loguru._logger import start_time, context as logger_context, Logger
    from types import MethodType

    _log = logger._log
    log_reporter_level = logging.getLevelName(config.agent_log_reporter_level)  # type: int

    def gen_record(self, level_id, static_level_no, from_decorator, options, message, args, kwargs):
        """ Generate log record as loguru.logger._log """
        core = self._core

        if not core.handlers:
            return

        (exception, depth, record, lazy, colors, raw, capture, patcher, extra) = options

        frame = get_frame(depth + 2)

        try:
            name = frame.f_globals['__name__']
        except KeyError:
            name = None

        try:
            if not core.enabled[name]:
                return
        except KeyError:
            enabled = core.enabled
            if name is None:
                status = core.activation_none
                enabled[name] = status
                if not status:
                    return
            else:
                dotted_name = name + '.'
                for dotted_module_name, status in core.activation_list:
                    if dotted_name[: len(dotted_module_name)] == dotted_module_name:
                        if status:
                            break
                        enabled[name] = False
                        return
                enabled[name] = True

        current_datetime = aware_now()

        if level_id is None:
            level_icon = ' '
            level_no = static_level_no
            level_name = f'Level {level_no}'  # not really level name, just as loguru
        else:
            level_name, level_no, _, level_icon = core.levels[level_id]

        if level_no < core.min_level:
            return

        code = frame.f_code
        file_path = code.co_filename
        file_name = basename(file_path)
        thread = current_thread()
        process = current_process()
        elapsed = current_datetime - start_time

        if exception:
            if isinstance(exception, BaseException):
                type_, value, traceback = (type(exception), exception, exception.__traceback__)
            elif isinstance(exception, tuple):
                type_, value, traceback = exception
            else:
                type_, value, traceback = sys.exc_info()
            exception = RecordException(type_, value, traceback)
        else:
            exception = None

        log_record = {
            'elapsed': elapsed,
            'exception': exception,
            'extra': {**core.extra, **logger_context.get(), **extra},
            'file': RecordFile(file_name, file_path),
            'function': code.co_name,
            'level': RecordLevel(level_name, level_no, level_icon),
            'line': frame.f_lineno,
            'message': str(message),
            'module': splitext(file_name)[0],
            'name': name,
            'process': RecordProcess(process.ident, process.name),
            'thread': RecordThread(thread.ident, thread.name),
            'time': current_datetime,
        }

        if capture and kwargs:
            log_record['extra'].update(kwargs)

        if record:
            kwargs.update(record=log_record)

        if args or kwargs:
            log_record['message'] = message.format(*args, **kwargs)

        if core.patcher:
            core.patcher(log_record)

        if patcher:
            patcher(log_record)

        return log_record

    def _sw_log(self, level_id, static_level_no, from_decorator, options, message, args, kwargs):
        _log(level_id, static_level_no, from_decorator, options, message, args, kwargs)
        record = gen_record(self, level_id, static_level_no, from_decorator, options, message, args, kwargs)
        if record is None:
            return

        core = self._core

        if record['level'].no < log_reporter_level:
            return

        if not config.agent_log_reporter_ignore_filter and record['level'].no < core.min_level:  # ignore filtered logs
            return

        # loguru has only one logger. Use tags referring Python-Agent doc
        core_tags = [
            KeyStringValuePair(key='level', value=record['level'].name),
            KeyStringValuePair(key='logger', value='loguru'),
            KeyStringValuePair(key='thread', value=record['thread'].name),
        ]
        tags = LogTags()
        tags.data.extend(core_tags)

        exception = record['exception']
        if exception:
            stack_trace = ''.join(traceback.format_exception(exception.type, exception.value, exception.traceback,
                                                             limit=config.agent_cause_exception_depth))
            tags.data.append(KeyStringValuePair(key='exception',
                                                value=sw_filter(stack_trace)
                                                ))  # \n doesn't work in tags for UI

        context = get_context()

        active_span_id = -1
        primary_endpoint_name = ''

        try:
            # Try to extract active span, if user code/plugin code throws uncaught
            # exceptions before any span is even created, just ignore these fields and
            # avoid appending 'no active span' traceback that could be confusing.
            # Or simply the log is generated outside any span context.
            active_span_id = context.active_span.sid
            primary_endpoint_name = context.primary_endpoint.get_name()
        except IllegalStateError:
            pass

        log_data = LogData(
            timestamp=round(record['time'].timestamp() * 1000),
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
            body=LogDataBody(
                type='text',
                text=TextLog(
                    text=sw_filter(message)
                )
            ),
            tags=tags,
        )

        if active_span_id != -1:
            trace_context = TraceContext(
                traceId=str(context.segment.related_traces[0]),
                traceSegmentId=str(context.segment.segment_id),
                spanId=active_span_id
            )
            log_data.traceContext.CopyFrom(trace_context)

        if primary_endpoint_name:
            log_data.endpoint = primary_endpoint_name

        agent.archive_log(log_data)

    # Bind _sw_log function to default logger instance.
    bound_sw_log = MethodType(_sw_log, logger)
    logger._log = bound_sw_log
    # Bind _sw_log function to Logger class for new instance.
    Logger._log = _sw_log
