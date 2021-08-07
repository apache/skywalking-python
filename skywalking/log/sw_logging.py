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

from skywalking import config, agent
from skywalking.protocol.common.Common_pb2 import KeyStringValuePair
from skywalking.protocol.logging.Logging_pb2 import LogData, LogDataBody, TraceContext, LogTags, TextLog
from skywalking.trace.context import get_context


def install():
    from logging import Logger

    _handle = Logger.handle
    log_reporter_level = logging.getLevelName(config.log_grpc_reporter_level)

    def _sw_handle(self, record):
        if self.name == "skywalking":  # Ignore SkyWalking internal logger
            return _handle(self, record)

        if record.levelno < log_reporter_level:
            return _handle(self, record)

        def build_log_tags():
            core_tags = [
                KeyStringValuePair(key='level', value=str(record.levelname)),
                KeyStringValuePair(key='logger', value=str(record.name)),
                KeyStringValuePair(key='thread', value=str(record.threadName))
            ]
            l_tags = LogTags()
            l_tags.data.extend(core_tags)

            if config.log_grpc_reporter_formatted:
                return l_tags

            args = record.args
            for i, arg in enumerate(args):
                l_tags.data.append(KeyStringValuePair(key='argument.' + str(i), value=str(arg)))

            if record.exc_info:
                l_tags.data.append(KeyStringValuePair(key='exception', value=str(record.exc_info)))

            return l_tags

        context = get_context()

        log_data = LogData(
            timestamp=round(record.created * 1000),
            service=config.service_name,
            serviceInstance=config.service_instance,
            body=LogDataBody(
                type='text',
                text=TextLog(
                    text=transform(record)
                )
            ),
            traceContext=TraceContext(
                traceId=str(context.segment.related_traces[0]),
                traceSegmentId=str(context.segment.segment_id),
                spanId=context.active_span().sid if context.active_span() else -1
            ),
            tags=build_log_tags(),
        )

        _handle(self=self, record=record)

        agent.archive_log(log_data)

    Logger.handle = _sw_handle

    def transform(record):
        if config.log_grpc_reporter_formatted:
            layout = config.log_grpc_reporter_layout
            if layout:
                from logging import Formatter
                formatter = Formatter(fmt=layout)
                return formatter.format(record=record)
            return record.getMessage()

        return record.msg
