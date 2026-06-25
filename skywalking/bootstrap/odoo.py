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
from urllib.parse import urlsplit

from skywalking import config
from skywalking.loggings import logger


def maybe_start():
    agent_name = os.getenv('SW_AGENT_NAME', '').strip()
    backend = os.getenv('SW_AGENT_COLLECTOR_BACKEND_SERVICES', '').strip()
    if not agent_name or not backend:
        return False

    backend, force_tls = _normalize_backend(backend)
    config.agent_protocol = 'http'
    config.agent_name = agent_name
    config.agent_collector_backend_services = backend
    config.agent_force_tls = force_tls
    try:
        _start_agent()
        return True
    except Exception:
        logger.debug('SkyWalking Odoo bootstrap failed, continue without agent.', exc_info=True)
        return False


def _normalize_backend(backend):
    parsed = urlsplit(backend)
    if parsed.scheme in ('http', 'https') and parsed.netloc:
        return parsed.netloc + parsed.path.rstrip('/'), parsed.scheme == 'https'

    return backend.rstrip('/'), False


def _start_agent():
    from skywalking.agent import agent
    agent.start()
