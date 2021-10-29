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

from skywalking import Layer, Component, config
from skywalking.trace.context import get_context
from skywalking.trace.tags import TagDbType, TagDbStatement

link_vector = ['https://github.com/elastic/elasticsearch-py']
support_matrix = {
    'elasticsearch': {
        '>=3.6': ['7.13', '7.14', '7.15'],
    }
}
note = """"""


def install():
    from elasticsearch import Transport
    _perform_request = Transport.perform_request

    def _sw_perform_request(this: Transport, method, url, headers=None, params=None, body=None):
        context = get_context()
        peer = ','.join([f"{host['host']}:{str(host['port'])}" for host in this.hosts])
        with context.new_exit_span(op=f'Elasticsearch/{method}{url}', peer=peer,
                                   component=Component.Elasticsearch) as span:
            span.layer = Layer.Database
            res = _perform_request(this, method, url, headers=headers, params=params, body=body)

            span.tag(TagDbType('Elasticsearch'))
            if config.elasticsearch_trace_dsl:
                span.tag(TagDbStatement('' if body is None else body))

            return res

    Transport.perform_request = _sw_perform_request
