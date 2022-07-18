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
import re
import uuid

# Change to future after Python3.6 support ends
from typing import List, Pattern

QUEUE_TIMEOUT: int = 1

RE_IGNORE_PATH: Pattern = re.compile('^$')
RE_HTTP_IGNORE_METHOD: Pattern = RE_IGNORE_PATH

options = None  # here to include 'options' in globals
options = globals().copy()  # THIS MUST PRECEDE DIRECTLY BEFORE LIST OF CONFIG OPTIONS!

# Core level configurations
service_name: str = os.getenv('SW_AGENT_NAME') or 'Python Service Name'
service_instance: str = os.getenv('SW_AGENT_INSTANCE') or str(uuid.uuid1()).replace('-', '')
agent_namespace: str = os.getenv('SW_AGENT_NAMESPACE')
collector_address: str = os.getenv('SW_AGENT_COLLECTOR_BACKEND_SERVICES') or '127.0.0.1:11800'
kafka_bootstrap_servers: str = os.getenv('SW_KAFKA_REPORTER_BOOTSTRAP_SERVERS') or 'localhost:9092'
kafka_topic_management: str = os.getenv('SW_KAFKA_REPORTER_TOPIC_MANAGEMENT') or 'skywalking-managements'
kafka_topic_segment: str = os.getenv('SW_KAFKA_REPORTER_TOPIC_SEGMENT') or 'skywalking-segments'
kafka_topic_log: str = os.getenv('SW_KAFKA_REPORTER_TOPIC_LOG') or 'skywalking-logs'
force_tls: bool = os.getenv('SW_AGENT_FORCE_TLS', '').lower() == 'true'
protocol: str = (os.getenv('SW_AGENT_PROTOCOL') or 'grpc').lower()
authentication: str = os.getenv('SW_AGENT_AUTHENTICATION')
logging_level: str = os.getenv('SW_AGENT_LOGGING_LEVEL') or 'INFO'
disable_plugins: List[str] = (os.getenv('SW_AGENT_DISABLE_PLUGINS') or '').split(',')
max_buffer_size: int = int(os.getenv('SW_AGENT_MAX_BUFFER_SIZE', '10000'))
trace_ignore_path: str = os.getenv('SW_TRACE_IGNORE_PATH') or ''
ignore_suffix: str = os.getenv('SW_IGNORE_SUFFIX') or '.jpg,.jpeg,.js,.css,.png,.bmp,.gif,.ico,.mp3,' \
                                                      '.mp4,.html,.svg '
correlation_element_max_number: int = int(os.getenv('SW_CORRELATION_ELEMENT_MAX_NUMBER') or '3')
correlation_value_max_length: int = int(os.getenv('SW_CORRELATION_VALUE_MAX_LENGTH') or '128')

# Plugin configurations
sql_parameters_length: int = int(os.getenv('SW_SQL_PARAMETERS_LENGTH') or '0')
pymongo_trace_parameters: bool = os.getenv('SW_PYMONGO_TRACE_PARAMETERS') == 'True'
pymongo_parameters_max_length: int = int(os.getenv('SW_PYMONGO_PARAMETERS_MAX_LENGTH') or '512')
elasticsearch_trace_dsl: bool = os.getenv('SW_ELASTICSEARCH_TRACE_DSL') == 'True'

http_params_length_threshold: int = int(os.getenv('SW_HTTP_PARAMS_LENGTH_THRESHOLD') or '1024')
http_ignore_method: str = os.getenv('SW_HTTP_IGNORE_METHOD', '').upper()
flask_collect_http_params: bool = os.getenv('SW_FLASK_COLLECT_HTTP_PARAMS') == 'True'
sanic_collect_http_params: bool = os.getenv('SW_SANIC_COLLECT_HTTP_PARAMS') == 'True'
django_collect_http_params: bool = os.getenv('SW_DJANGO_COLLECT_HTTP_PARAMS') == 'True'
fastapi_collect_http_params: bool = os.getenv('SW_FASTAPI_COLLECT_HTTP_PARAMS') == 'True'
bottle_collect_http_params: bool = os.getenv('SW_BOTTLE_COLLECT_HTTP_PARAMS') == 'True'

celery_parameters_length: int = int(os.getenv('SW_CELERY_PARAMETERS_LENGTH') or '512')

# profiling configurations
get_profile_task_interval: int = int(os.getenv('SW_PROFILE_TASK_QUERY_INTERVAL') or '20')
profile_active: bool = os.getenv('SW_AGENT_PROFILE_ACTIVE') != 'False'
profile_max_parallel: int = int(os.getenv('SW_AGENT_PROFILE_MAX_PARALLEL') or '5')
profile_duration: int = int(os.getenv('SW_AGENT_PROFILE_DURATION') or '10')
profile_dump_max_stack_depth: int = int(os.getenv('SW_AGENT_PROFILE_DUMP_MAX_STACK_DEPTH') or '500')
profile_snapshot_transport_buffer_size: int = int(os.getenv('SW_AGENT_PROFILE_SNAPSHOT_TRANSPORT_BUFFER_SIZE') or '50')

# log reporter configurations
log_reporter_active: bool = os.getenv('SW_AGENT_LOG_REPORTER_ACTIVE') == 'True'
log_reporter_safe_mode: bool = os.getenv('SW_AGENT_LOG_REPORTER_SAFE_MODE') == 'True'
log_reporter_max_buffer_size: int = int(os.getenv('SW_AGENT_LOG_REPORTER_BUFFER_SIZE') or '10000')
log_reporter_level: str = os.getenv('SW_AGENT_LOG_REPORTER_LEVEL') or 'WARNING'
log_reporter_ignore_filter: bool = os.getenv('SW_AGENT_LOG_REPORTER_IGNORE_FILTER') == 'True'
log_reporter_formatted: bool = os.getenv('SW_AGENT_LOG_REPORTER_FORMATTED') != 'False'
log_reporter_layout: str = os.getenv('SW_AGENT_LOG_REPORTER_LAYOUT') or \
                           '%(asctime)s [%(threadName)s] %(levelname)s %(name)s - %(message)s'
# This configuration is shared by log reporter and tracer
cause_exception_depth: int = int(os.getenv('SW_AGENT_CAUSE_EXCEPTION_DEPTH') or '10')

options = {key for key in globals() if key not in options}  # THIS MUST FOLLOW DIRECTLY AFTER LIST OF CONFIG OPTIONS!


def init(**kwargs):
    glob = globals()

    for key, val in kwargs.items():
        if key not in options:
            raise KeyError(f'invalid config option {key}')

        glob[key] = val


def finalize():
    reesc = re.compile(r'([.*+?^=!:${}()|\[\]\\])')
    suffix = r'^.+(?:' + '|'.join(reesc.sub(r'\\\1', s.strip()) for s in ignore_suffix.split(',')) + ')$'
    method = r'^' + '|'.join(s.strip() for s in http_ignore_method.split(',')) + '$'
    path = '^(?:' + \
           '|'.join(  # replaces ","
               '/(?:[^/]*/)*'.join(  # replaces "/**/"
                   '(?:(?:[^/]+/)*[^/]+)?'.join(  # replaces "**"
                       '[^/]*'.join(  # replaces "*"
                           '[^/]'.join(  # replaces "?"
                               reesc.sub(r'\\\1', s) for s in p3.split('?')
                           ) for p3 in p2.split('*')
                       ) for p2 in p1.strip().split('**')
                   ) for p1 in p0.split('/**/')
               ) for p0 in trace_ignore_path.split(',')
           ) + ')$'

    global RE_IGNORE_PATH, RE_HTTP_IGNORE_METHOD
    RE_IGNORE_PATH = re.compile(f'{suffix}|{path}')
    RE_HTTP_IGNORE_METHOD = re.compile(method, re.IGNORECASE)


def ignore_http_method_check(method: str):
    return RE_HTTP_IGNORE_METHOD.match(method)
