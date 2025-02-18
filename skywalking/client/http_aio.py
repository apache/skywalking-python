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
import json
import aiohttp
from google.protobuf import json_format

from skywalking import config
from skywalking.client import ServiceManagementClientAsync, TraceSegmentReportServiceAsync, LogDataReportServiceAsync
from skywalking.loggings import logger, logger_debug_enabled


class HttpServiceManagementClientAsync(ServiceManagementClientAsync):
    def __init__(self):
        super().__init__()
        self.instance_properties = self.get_instance_properties()

        proto = 'https://' if config.agent_force_tls else 'http://'
        self.url_instance_props = f"{proto}{config.agent_collector_backend_services.rstrip('/')}/v3/management/reportProperties"
        self.url_heart_beat = f"{proto}{config.agent_collector_backend_services.rstrip('/')}/v3/management/keepAlive"
        # self.client = httpx.AsyncClient()
        self.client = aiohttp.ClientSession()

    async def send_instance_props(self):

        async with self.client as client:
            res = await client.post(self.url_instance_props, json={
                'service': config.agent_name,
                'serviceInstance': config.agent_instance_name,
                'properties': self.instance_properties,
            })
        if logger_debug_enabled:
            logger.debug('heartbeat response: %s', res)

    async def send_heart_beat(self):
        await self.refresh_instance_props()

        if logger_debug_enabled:
            logger.debug(
                'service heart beats, [%s], [%s]',
                config.agent_name,
                config.agent_instance_name,
            )
        async with self.client as client:
            res = await client.post(self.url_heart_beat, json={
                'service': config.agent_name,
                'serviceInstance': config.agent_instance_name,
            })
        if logger_debug_enabled:
            logger.debug('heartbeat response: %s', res)


class HttpTraceSegmentReportServiceAsync(TraceSegmentReportServiceAsync):
    def __init__(self):
        proto = 'https://' if config.agent_force_tls else 'http://'
        self.url_report = f"{proto}{config.agent_collector_backend_services.rstrip('/')}/v3/segment"
        # self.client = httpx.AsyncClient()
        self.client = aiohttp.ClientSession()

    async def report(self, generator):
        async for segment in generator:
            async with self.client as client:
                res = await client.post(self.url_report, json={
                    'traceId': str(segment.related_traces[0]),
                    'traceSegmentId': str(segment.segment_id),
                    'service': config.agent_name,
                    'serviceInstance': config.agent_instance_name,
                    'isSizeLimited': segment.is_size_limited,
                    'spans': [{
                        'spanId': span.sid,
                        'parentSpanId': span.pid,
                        'startTime': span.start_time,
                        'endTime': span.end_time,
                        'operationName': span.op,
                        'peer': span.peer,
                        'spanType': span.kind.name,
                        'spanLayer': span.layer.name,
                        'componentId': span.component.value,
                        'isError': span.error_occurred,
                        'logs': [{
                            'time': int(log.timestamp * 1000),
                            'data': [{
                                'key': item.key,
                                'value': item.val,
                            } for item in log.items],
                        } for log in span.logs],
                        'tags': [{
                            'key': tag.key,
                            'value': tag.val,
                        } for tag in span.iter_tags()],
                        'refs': [{
                            'refType': 0,
                            'traceId': ref.trace_id,
                            'parentTraceSegmentId': ref.segment_id,
                            'parentSpanId': ref.span_id,
                            'parentService': ref.service,
                            'parentServiceInstance': ref.service_instance,
                            'parentEndpoint': ref.endpoint,
                            'networkAddressUsedAtPeer': ref.client_address,
                        } for ref in span.refs if ref.trace_id]
                    } for span in segment.spans]
                })
            if logger_debug_enabled:
                logger.debug('report traces response: %s', res)


class HttpLogDataReportServiceAsync(LogDataReportServiceAsync):
    def __init__(self):
        proto = 'https://' if config.agent_force_tls else 'http://'
        self.url_report = f"{proto}{config.agent_collector_backend_services.rstrip('/')}/v3/logs"
        # self.client = httpx.AsyncClient()
        self.client = aiohttp.ClientSession()

    async def report(self, generator):
        log_batch = [json.loads(json_format.MessageToJson(log_data)) async for log_data in generator]
        if log_batch:  # prevent empty batches
            async with self.client as client:
                res = await client.post(self.url_report, json=log_batch)
            if logger_debug_enabled:
                logger.debug('report batch log response: %s', res)
