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
        '>=3.7': ['0.6.0', '0.7.0']
    }
}
note = """"""


def install():
    if not config.agent_log_reporter_active:
        return

    from loguru import logger

    log_reporter_level = logging.getLevelName(config.agent_log_reporter_level)  # type: int

    def _sw_sink(message):
        record = message.record

        if record is None:
            return

        if record['level'].no < log_reporter_level:
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
            # But actually NO need to raise and catch IllegalStateError here.
            active_span = context.active_span
            if active_span is not None:
                active_span_id = active_span.sid
                primary_endpoint_name = context.primary_endpoint.get_name() if context.primary_endpoint else ''
        except IllegalStateError:
            pass

        log_data = LogData(
            timestamp=round(record['time'].timestamp() * 1000),
            service=config.agent_name,
            serviceInstance=config.agent_instance_name,
            body=LogDataBody(
                type='text',
                text=TextLog(
                    text=sw_filter(record['message'])
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

    # Make sure any logged message by loguru is also sent to skywalking OAP
    logger.add(_sw_sink)
