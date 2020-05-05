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

import os
import uuid

service_name = os.getenv('SW_AGENT_NAME') or 'Python Service Name'  # type: str
service_instance = os.getenv('SW_AGENT_INSTANCE') or str(uuid.uuid1()).replace('-', '')  # type: str
collector_address = os.getenv('SW_AGENT_COLLECTOR_BACKEND_SERVICES') or '127.0.0.1:11800'  # type: str
protocol = os.getenv('SW_AGENT_PROTOCOL') or 'grpc'  # type: str


def init(
        service: str = None,
        instance: str = None,
        collector: str = None,
        protocol_type: str = 'grpc',
):
    global service_name
    service_name = service or service_name

    global service_instance
    service_instance = instance or service_instance

    global collector_address
    collector_address = collector or collector_address

    global protocol
    protocol = protocol_type or protocol
