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

import requests

from skywalking import config
from skywalking.client import ServiceManagementClient, TraceSegmentReportService

logger = logging.getLogger(__name__)


class HttpServiceManagementClient(ServiceManagementClient):
    def __init__(self):
        self.session = requests.session()

    def send_instance_props(self):
        url = config.collector_address.rstrip('/') + '/v3/management/reportProperties'
        res = self.session.post(url, json={
            'service': config.service_name,
            'serviceInstance': config.service_instance,
            'properties': [{
                'language': 'Python',
            }]
        })
        logger.debug('heartbeat response: %s', res)

    def send_heart_beat(self):
        logger.debug(
            'service heart beats, [%s], [%s]',
            config.service_name,
            config.service_instance,
        )
        url = config.collector_address.rstrip('/') + '/v3/management/keepAlive'
        res = self.session.post(url, json={
            'service': config.service_name,
            'serviceInstance': config.service_instance,
        })
        logger.debug('heartbeat response: %s', res)


class HttpTraceSegmentReportService(TraceSegmentReportService):
    def __init__(self):
        self.session = requests.session()

    def report(self, generator):
        url = config.collector_address.rstrip('/') + '/v3/segment'
        for segment in generator:
            res = self.session.post(url, json={
                'traceId': str(segment.related_traces[0]),
                'traceSegmentId': str(segment.segment_id),
                'service': config.service_name,
                'serviceInstance': config.service_instance,
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
                        'time': log.timestamp * 1000,
                        'data': [{
                            'key': item.key,
                            'value': item.val
                        } for item in log.items],
                    } for log in span.logs],
                    'tags': [{
                        'key': tag.key,
                        'value': tag.val,
                    } for tag in span.tags],
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
            logger.debug('report traces response: %s', res)
