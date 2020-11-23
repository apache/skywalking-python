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
from skywalking.trace import tags
from skywalking.trace.context import get_context
from skywalking.trace.tags import Tag


def install():
    from elasticsearch import Transport
    _perform_request = Transport.perform_request

    def _sw_perform_request(this: Transport, method, url, headers=None, params=None, body=None):
        context = get_context()
        peer = ",".join([host["host"] + ":" + str(host["port"]) for host in this.hosts])
        with context.new_exit_span(op="Elasticsearch/" + method + url, peer=peer) as span:
            span.layer = Layer.Database
            span.component = Component.Elasticsearch
            res = _perform_request(this, method, url, headers=headers, params=params, body=body)

            span.tag(Tag(key=tags.DbType, val="Elasticsearch"))
            if config.elasticsearch_trace_dsl:
                span.tag(Tag(key=tags.DbStatement, val="" if body is None else body))

            return res

    Transport.perform_request = _sw_perform_request
