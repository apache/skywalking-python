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

from skywalking import config
from skywalking.agent import agent
from skywalking.protocol.common.Common_pb2 import KeyStringValuePair
from skywalking.protocol.logging.Logging_pb2 import LogData, LogDataBody, TraceContext, LogTags, TextLog
from skywalking.trace.context import get_context
from skywalking.utils.exception import IllegalStateError
from skywalking.utils.filter import sw_traceback, sw_filter


def install():
    from logging import Logger

    layout = config.agent_log_reporter_layout  # type: str
    if layout:
        from skywalking.log.formatter import SWFormatter
        sw_formatter = SWFormatter(fmt=layout, tb_limit=config.agent_cause_exception_depth)

    _handle = Logger.handle
    log_reporter_level = logging.getLevelName(config.agent_log_reporter_level)  # type: int

    def _sw_handle(self, record):
        _handle(self=self, record=record)

        if self.disabled:
            return

        if record.name in ['skywalking', 'skywalking-cli', 'skywalking-loader']:  # Ignore SkyWalking internal loggers
            return

        if record.levelno < log_reporter_level:
            return

        if not config.agent_log_reporter_ignore_filter and not self.filter(record):  # ignore filtered logs
            return

        def build_log_tags() -> LogTags:
            core_tags = [
                KeyStringValuePair(key='level', value=str(record.levelname)),
                KeyStringValuePair(key='logger', value=str(record.name)),
                KeyStringValuePair(key='thread', value=str(record.threadName))
            ]
            l_tags = LogTags()
            l_tags.data.extend(core_tags)

            if config.agent_log_reporter_formatted:
                return l_tags

            for i, arg in enumerate(record.args):
                l_tags.data.append(KeyStringValuePair(key=f'argument.{str(i)}', value=str(arg)))

            if record.exc_info:
                l_tags.data.append(KeyStringValuePair(key='exception',
                                                      value=sw_traceback()
                                                      ))  # \n doesn't work in tags for UI
            return l_tags

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
            timestamp=round(record.created * 1000),
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
            body=LogDataBody(
                type='text',
                text=TextLog(
                    text=sw_filter(transform(record))
                )
            ),
            tags=build_log_tags(),
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

    Logger.handle = _sw_handle

    def transform(record) -> str:
        if config.agent_log_reporter_formatted:
            if layout:
                return sw_formatter.format(record=record)
            newline = '\n'
            return f"{record.getMessage()}{f'{newline}{sw_traceback()}' if record.exc_info else ''}"
        return str(record.msg)  # convert possible exception to str
