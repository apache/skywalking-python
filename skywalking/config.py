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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List

QUEUE_TIMEOUT = 1  # type: int

RE_IGNORE_PATH = re.compile('^$')  # type: re.Pattern
RE_HTTP_IGNORE_METHOD = RE_IGNORE_PATH  # type: re.Pattern

options = None  # here to include 'options' in globals
options = globals().copy()  # THIS MUST PRECEDE DIRECTLY BEFORE LIST OF CONFIG OPTIONS!

service_name = os.getenv('SW_AGENT_NAME') or 'Python Service Name'  # type: str
service_instance = os.getenv('SW_AGENT_INSTANCE') or str(uuid.uuid1()).replace('-', '')  # type: str
agent_namespace = os.getenv('SW_AGENT_NAMESPACE')  # type: str
collector_address = os.getenv('SW_AGENT_COLLECTOR_BACKEND_SERVICES') or '127.0.0.1:11800'  # type: str
force_tls = os.getenv('SW_AGENT_FORCE_TLS', '').lower() == 'true'  # type: bool
protocol = (os.getenv('SW_AGENT_PROTOCOL') or 'grpc').lower()  # type: str
authentication = os.getenv('SW_AGENT_AUTHENTICATION')  # type: str
logging_level = os.getenv('SW_AGENT_LOGGING_LEVEL') or 'INFO'  # type: str
disable_plugins = (os.getenv('SW_AGENT_DISABLE_PLUGINS') or '').split(',')  # type: List[str]
max_buffer_size = int(os.getenv('SW_AGENT_MAX_BUFFER_SIZE', '10000'))  # type: int
sql_parameters_length = int(os.getenv('SW_SQL_PARAMETERS_LENGTH') or '0')  # type: int
pymongo_trace_parameters = True if os.getenv('SW_PYMONGO_TRACE_PARAMETERS') and \
                                   os.getenv('SW_PYMONGO_TRACE_PARAMETERS') == 'True' else False  # type: bool
pymongo_parameters_max_length = int(os.getenv('SW_PYMONGO_PARAMETERS_MAX_LENGTH') or '512')  # type: int
ignore_suffix = os.getenv('SW_IGNORE_SUFFIX') or '.jpg,.jpeg,.js,.css,.png,.bmp,.gif,.ico,.mp3,' \
                                                 '.mp4,.html,.svg '  # type: str
flask_collect_http_params = True if os.getenv('SW_FLASK_COLLECT_HTTP_PARAMS') and \
                                    os.getenv('SW_FLASK_COLLECT_HTTP_PARAMS') == 'True' else False  # type: bool
sanic_collect_http_params = True if os.getenv('SW_SANIC_COLLECT_HTTP_PARAMS') and \
                                    os.getenv('SW_SANIC_COLLECT_HTTP_PARAMS') == 'True' else False  # type: bool
http_params_length_threshold = int(os.getenv('SW_HTTP_PARAMS_LENGTH_THRESHOLD') or '1024')  # type: int
http_ignore_method = os.getenv('SW_HTTP_IGNORE_METHOD', '').upper()  # type: str
django_collect_http_params = True if os.getenv('SW_DJANGO_COLLECT_HTTP_PARAMS') and \
                                     os.getenv('SW_DJANGO_COLLECT_HTTP_PARAMS') == 'True' else False  # type: bool
correlation_element_max_number = int(os.getenv('SW_CORRELATION_ELEMENT_MAX_NUMBER') or '3')  # type: int
correlation_value_max_length = int(os.getenv('SW_CORRELATION_VALUE_MAX_LENGTH') or '128')  # type: int
trace_ignore_path = os.getenv('SW_TRACE_IGNORE_PATH') or ''  # type: str
elasticsearch_trace_dsl = True if os.getenv('SW_ELASTICSEARCH_TRACE_DSL') and \
                                  os.getenv('SW_ELASTICSEARCH_TRACE_DSL') == 'True' else False  # type: bool
kafka_bootstrap_servers = os.getenv('SW_KAFKA_REPORTER_BOOTSTRAP_SERVERS') or 'localhost:9092'  # type: str
kafka_topic_management = os.getenv('SW_KAFKA_REPORTER_TOPIC_MANAGEMENT') or 'skywalking-managements'  # type: str
kafka_topic_segment = os.getenv('SW_KAFKA_REPORTER_TOPIC_SEGMENT') or 'skywalking-segments'  # type: str
kafka_topic_log = os.getenv('SW_KAFKA_REPORTER_TOPIC_LOG') or 'skywalking-logs'  # type: str
celery_parameters_length = int(os.getenv('SW_CELERY_PARAMETERS_LENGTH') or '512')
fastapi_collect_http_params = True if os.getenv('SW_FASTAPI_COLLECT_HTTP_PARAMS') and \
                                      os.getenv('SW_FASTAPI_COLLECT_HTTP_PARAMS') == 'True' else False  # type: bool

# profile configs
get_profile_task_interval = int(os.getenv('SW_PROFILE_TASK_QUERY_INTERVAL') or '20')  # type: int
profile_active = False if os.getenv('SW_AGENT_PROFILE_ACTIVE') and \
                          os.getenv('SW_AGENT_PROFILE_ACTIVE') == 'False' else True  # type: bool
profile_max_parallel = int(os.getenv('SW_AGENT_PROFILE_MAX_PARALLEL') or '5')  # type: int
profile_duration = int(os.getenv('SW_AGENT_PROFILE_DURATION') or '10')  # type: int
profile_dump_max_stack_depth = int(os.getenv('SW_AGENT_PROFILE_DUMP_MAX_STACK_DEPTH') or '500')  # type: int
profile_snapshot_transport_buffer_size = int(os.getenv('SW_AGENT_PROFILE_SNAPSHOT_TRANSPORT_BUFFER_SIZE') or '50')

log_reporter_active = True if os.getenv('SW_AGENT_LOG_REPORTER_ACTIVE') and \
                              os.getenv('SW_AGENT_LOG_REPORTER_ACTIVE') == 'True' else False  # type: bool
log_reporter_max_buffer_size = int(os.getenv('SW_AGENT_LOG_REPORTER_BUFFER_SIZE') or '10000')  # type: int
log_reporter_level = os.getenv('SW_AGENT_LOG_REPORTER_LEVEL') or 'WARNING'  # type: str
log_reporter_ignore_filter = True if os.getenv('SW_AGENT_LOG_REPORTER_IGNORE_FILTER') and \
                                     os.getenv('SW_AGENT_LOG_REPORTER_IGNORE_FILTER') == 'True' else False  # type: bool
log_reporter_formatted = False if os.getenv('SW_AGENT_LOG_REPORTER_FORMATTED') and \
                                  os.getenv('SW_AGENT_LOG_REPORTER_FORMATTED') == 'False' else True  # type: bool
log_reporter_layout = os.getenv('SW_AGENT_LOG_REPORTER_LAYOUT') or \
                      '%(asctime)s [%(threadName)s] %(levelname)s %(name)s - %(message)s'  # type: str
cause_exception_depth = int(os.getenv('SW_AGENT_CAUSE_EXCEPTION_DEPTH') or '5')  # type: int


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
               '(?:(?:[^/]+/)*[^/]+)?'.join(  # replaces "**"
                   '[^/]*'.join(  # replaces "*"
                       '[^/]'.join(  # replaces "?"
                           reesc.sub(r'\\\1', s) for s in p2.split('?')
                       ) for p2 in p1.split('*')
                   ) for p1 in p0.strip().split('**')
               ) for p0 in trace_ignore_path.split(',')
           ) + ')$'

    global RE_IGNORE_PATH, RE_HTTP_IGNORE_METHOD
    RE_IGNORE_PATH = re.compile(f'{suffix}|{path}')
    RE_HTTP_IGNORE_METHOD = re.compile(method, re.IGNORECASE)


def ignore_http_method_check(method: str):
    return RE_HTTP_IGNORE_METHOD.match(method)
