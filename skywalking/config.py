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
"""
This module holds all the configuration options for the agent. The options are loaded from both environment variables and
through code level, default values are provided for each option.

The environment variables must be named as `SW_AGENT_<option_variable>`.

Contributors attention: When adding an new configuration option, please precede each option with a comment like this:
# This option does bla bla
# could be multiple lines
actual_option: str = os.getenv('SW_AGENT_ACTUAL_OPTION') or 'default_value'

The comments along with each option will be used to generate the documentation for the agent, you don't need to modify
any documentation to reflect changes here, just make sure to run `make doc-gen` to generate the documentation.
"""

import os
import re
import uuid
import warnings
from typing import List, Pattern

RE_IGNORE_PATH: Pattern = re.compile('^$')
RE_HTTP_IGNORE_METHOD: Pattern = RE_IGNORE_PATH
RE_GRPC_IGNORED_METHODS: Pattern = RE_IGNORE_PATH

options = None  # here to include 'options' in globals
options = globals().copy()
# THIS MUST PRECEDE DIRECTLY BEFORE LIST OF CONFIG OPTIONS!

# BEGIN: Agent Core Configuration Options
# The backend OAP server address, 11800 is default OAP gRPC port, 12800 is HTTP, Kafka ignores this option
# and uses kafka_bootstrap_servers option. **This option should be changed accordingly with selected protocol**
agent_collector_backend_services: str = os.getenv('SW_AGENT_COLLECTOR_BACKEND_SERVICES', 'oap_host:oap_port')
# The protocol to communicate with the backend OAP, `http`, `grpc` or `kafka`, **we highly suggest using `grpc` in
# production as it's well optimized than `http`**. The `kafka` protocol provides an alternative way to submit data to
# the backend.
agent_protocol: str = os.getenv('SW_AGENT_PROTOCOL', 'grpc').lower()
# The name of your awesome Python service
agent_name: str = os.getenv('SW_AGENT_NAME', 'Python Service Name')
# The name of this particular awesome Python service instance
agent_instance_name: str = os.getenv('SW_AGENT_INSTANCE_NAME', str(uuid.uuid1()).replace('-', ''))
# The agent namespace of the Python service (available as tag and the suffix of service name)
agent_namespace: str = os.getenv('SW_AGENT_NAMESPACE', '')
# A list of host/port pairs to use for establishing the initial connection to your Kafka cluster.
# It is in the form of host1:port1,host2:port2,... (used for Kafka reporter protocol)
kafka_bootstrap_servers: str = os.getenv('SW_KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
# The kafka namespace specified by OAP side SW_NAMESPACE, prepends the following kafka topic names with a `-`.
kafka_namespace: str = os.getenv('SW_KAFKA_NAMESPACE', '')
# Specifying Kafka topic name for service instance reporting and registering, this should be in sync with OAP
kafka_topic_management: str = os.getenv('SW_KAFKA_TOPIC_MANAGEMENT', 'skywalking-managements')
# Specifying Kafka topic name for Tracing data, this should be in sync with OAP
kafka_topic_segment: str = os.getenv('SW_KAFKA_TOPIC_SEGMENT', 'skywalking-segments')
# Specifying Kafka topic name for Log data, this should be in sync with OAP
kafka_topic_log: str = os.getenv('SW_KAFKA_TOPIC_LOG', 'skywalking-logs')
# Specifying Kafka topic name for Meter data, this should be in sync with OAP
kafka_topic_meter: str = os.getenv('SW_KAFKA_TOPIC_METER', 'skywalking-meters')
# The configs to init KafkaProducer, supports the basic arguments (whose type is either `str`, `bool`, or `int`) listed
# [here](https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html#kafka.KafkaProducer)
# This config only works from env variables, each one should be passed in `SW_KAFKA_REPORTER_CONFIG_<KEY_NAME>`
kafka_reporter_custom_configurations: str = os.getenv('SW_KAFKA_REPORTER_CUSTOM_CONFIGURATIONS', '')
# Use TLS for communication with SkyWalking OAP (no cert required)
agent_force_tls: bool = os.getenv('SW_AGENT_FORCE_TLS', '').lower() == 'true'
# The authentication token to verify that the agent is trusted by the backend OAP, as for how to configure the
# backend, refer to [the yaml](https://github.com/apache/skywalking/blob/4f0f39ffccdc9b41049903cc540b8904f7c9728e/
# oap-server/server-bootstrap/src/main/resources/application.yml#L155-L158).
agent_authentication: str = os.getenv('SW_AGENT_AUTHENTICATION', '')
# The level of agent self-logs, could be one of `CRITICAL`, `FATAL`, `ERROR`, `WARN`(`WARNING`), `INFO`, `DEBUG`.
# Please turn on debug if an issue is encountered to find out what's going on
agent_logging_level: str = os.getenv('SW_AGENT_LOGGING_LEVEL', 'INFO')

# BEGIN: Agent Core Danger Zone
# The agent will exchange heartbeat message with SkyWalking OAP backend every `period` seconds
agent_collector_heartbeat_period: int = int(os.getenv('SW_AGENT_COLLECTOR_HEARTBEAT_PERIOD', '30'))
# The agent will report service instance properties every
# `factor * heartbeat period` seconds default: 10*30 = 300 seconds
agent_collector_properties_report_period_factor = int(
    os.getenv('SW_AGENT_COLLECTOR_PROPERTIES_REPORT_PERIOD_FACTOR', '10'))
# A custom JSON string to be reported as service instance properties, e.g. `{"key": "value"}`
agent_instance_properties_json: str = os.getenv('SW_AGENT_INSTANCE_PROPERTIES_JSON', '')
# The agent will restart itself in any os.fork()-ed child process. Important Note: it's not suitable for
# short-lived processes as each one will create a new instance in SkyWalking dashboard
# in format of `service_instance-child(pid)`.
# This feature may not work when a precise combination of gRPC + Python 3.7 + subprocess (not fork) is used together.
# The agent will output a warning log when using on Python 3.7 for such a reason.
agent_experimental_fork_support: bool = os.getenv('SW_AGENT_EXPERIMENTAL_FORK_SUPPORT', '').lower() == 'true'
# DANGEROUS - This option controls the interval of each bulk report from telemetry data queues
# Do not modify unless you have evaluated its impact given your service load.
agent_queue_timeout: int = int(os.getenv('SW_AGENT_QUEUE_TIMEOUT', '1'))
# Replace the threads to asyncio coroutines to report telemetry data to the OAP.
# This option is experimental and may not work as expected.
agent_asyncio_enhancement: bool = os.getenv('SW_AGENT_ASYNCIO_ENHANCEMENT', '').lower() == 'true'

# BEGIN: SW_PYTHON Auto Instrumentation CLI
# Special: can only be passed via environment. This config controls the child process agent bootstrap behavior in
# `sw-python` CLI, if set to `False`, a valid child process will not boot up a SkyWalking Agent. Please refer to the
# [CLI Guide](CLI.md) for details.
agent_sw_python_bootstrap_propagate = os.getenv('SW_AGENT_SW_PYTHON_BOOTSTRAP_PROPAGATE', '').lower() == 'true'
# Special: can only be passed via environment. This config controls the CLI and agent logging debug mode, if set to
# `True`, the CLI and agent will print out debug logs. Please refer to the [CLI Guide](CLI.md) for details.
# Important: this config will set agent logging level to `DEBUG` as well, do not use it in production otherwise it will
# flood your logs. This normally shouldn't be pass as a simple flag -d will be the same.
agent_sw_python_cli_debug_enabled = os.getenv('SW_AGENT_SW_PYTHON_CLI_DEBUG_ENABLED', '').lower() == 'true'

# BEGIN: Trace Reporter Configurations
# The maximum queue backlog size for sending the segment data to backend, segments beyond this are silently dropped
agent_trace_reporter_max_buffer_size: int = int(os.getenv('SW_AGENT_TRACE_REPORTER_MAX_BUFFER_SIZE', '10000'))
# You can setup multiple URL path patterns, The endpoints match these patterns wouldn't be traced. the current
# matching rules follow Ant Path match style , like /path/*, /path/**, /path/?.
agent_trace_ignore_path: str = os.getenv('SW_AGENT_TRACE_IGNORE_PATH', '')
# If the operation name of the first span is included in this set, this segment should be ignored.
agent_ignore_suffix: str = os.getenv('SW_AGENT_IGNORE_SUFFIX', '.jpg,.jpeg,.js,.css,.png,.bmp,.gif,.ico,.mp3,'
                                                               '.mp4,.html,.svg ')
# Max element count of the correlation context.
correlation_element_max_number: int = int(os.getenv('SW_CORRELATION_ELEMENT_MAX_NUMBER', '3'))
# Max value length of correlation context element.
correlation_value_max_length: int = int(os.getenv('SW_CORRELATION_VALUE_MAX_LENGTH', '128'))

# BEGIN: Profiling Configurations
# If `True`, Python agent will enable profiler when user create a new profiling task.
agent_profile_active: bool = os.getenv('SW_AGENT_PROFILE_ACTIVE', '').lower() != 'false'
# The number of seconds between two profile task query.
agent_collector_get_profile_task_interval: int = int(os.getenv('SW_AGENT_COLLECTOR_GET_PROFILE_TASK_INTERVAL', '20'))
# The number of parallel monitor segment count.
agent_profile_max_parallel: int = int(os.getenv('SW_AGENT_PROFILE_MAX_PARALLEL', '5'))
# The maximum monitor segment time(minutes), if current segment monitor time out of limit, then stop it.
agent_profile_duration: int = int(os.getenv('SW_AGENT_PROFILE_DURATION', '10'))
# The number of max dump thread stack depth
agent_profile_dump_max_stack_depth: int = int(os.getenv('SW_AGENT_PROFILE_DUMP_MAX_STACK_DEPTH', '500'))
# The number of snapshot transport to backend buffer size
agent_profile_snapshot_transport_buffer_size: int = int(
    os.getenv('SW_AGENT_PROFILE_SNAPSHOT_TRANSPORT_BUFFER_SIZE', '50'))

# BEGIN: Log Reporter Configurations
# If `True`, Python agent will report collected logs to the OAP or Satellite. Otherwise, it disables the feature.
agent_log_reporter_active: bool = os.getenv('SW_AGENT_LOG_REPORTER_ACTIVE', '').lower() != 'false'
# If `True`, Python agent will filter out HTTP basic auth information from log records. By default, it disables the
# feature due to potential performance impact brought by regular expression
agent_log_reporter_safe_mode: bool = os.getenv('SW_AGENT_LOG_REPORTER_SAFE_MODE', '').lower() == 'true'
# The maximum queue backlog size for sending log data to backend, logs beyond this are silently dropped.
agent_log_reporter_max_buffer_size: int = int(os.getenv('SW_AGENT_LOG_REPORTER_MAX_BUFFER_SIZE', '10000'))
# This config specifies the logger levels of concern, any logs with a level below the config will be ignored.
agent_log_reporter_level: str = os.getenv('SW_AGENT_LOG_REPORTER_LEVEL', 'WARNING')
# This config customizes whether to ignore the application-defined logger filters, if `True`, all logs are reported
# disregarding any filter rules.
agent_log_reporter_ignore_filter: bool = os.getenv('SW_AGENT_LOG_REPORTER_IGNORE_FILTER', '').lower() == 'true'
# If `True`, the log reporter will transmit the logs as formatted. Otherwise, puts logRecord.msg and logRecord.args
# into message content and tags(`argument.n`), respectively. Along with an `exception` tag if an exception was raised.
# Only applies to logging module.
agent_log_reporter_formatted: bool = os.getenv('SW_AGENT_LOG_REPORTER_FORMATTED', '').lower() != 'false'
# The log reporter formats the logRecord message based on the layout given.
# Only applies to logging module.
agent_log_reporter_layout: str = os.getenv('SW_AGENT_LOG_REPORTER_LAYOUT',
                                           '%(asctime)s [%(threadName)s] %(levelname)s %(name)s - %(message)s')
# This configuration is shared by log reporter and tracer.
# This config limits agent to report up to `limit` stacktrace, please refer to [Python traceback](
# https://docs.python.org/3/library/traceback.html#traceback.print_tb) for more explanations.
agent_cause_exception_depth: int = int(os.getenv('SW_AGENT_CAUSE_EXCEPTION_DEPTH', '10'))

# BEGIN: Meter Reporter Configurations
# If `True`, Python agent will report collected meters to the OAP or Satellite. Otherwise, it disables the feature.
agent_meter_reporter_active: bool = os.getenv('SW_AGENT_METER_REPORTER_ACTIVE', '').lower() != 'false'
# The maximum queue backlog size for sending meter data to backend, meters beyond this are silently dropped.
agent_meter_reporter_max_buffer_size: int = int(os.getenv('SW_AGENT_METER_REPORTER_MAX_BUFFER_SIZE', '10000'))
# The interval in seconds between each meter data report
agent_meter_reporter_period: int = int(os.getenv('SW_AGENT_METER_REPORTER_PERIOD', '20'))
# If `True`, Python agent will report collected Python Virtual Machine (PVM) meters to the OAP or Satellite.
# Otherwise, it disables the feature.
agent_pvm_meter_reporter_active: bool = os.getenv('SW_AGENT_PVM_METER_REPORTER_ACTIVE', '').lower() != 'false'

# BEGIN: Plugin Related configurations
# The name patterns in comma-separated pattern, plugins whose name matches one of the pattern won't be installed
agent_disable_plugins: List[str] = os.getenv('SW_AGENT_DISABLE_PLUGINS', '').split(',')
# When `COLLECT_HTTP_PARAMS` is enabled, how many characters to keep and send to the OAP backend, use negative
# values to keep and send the complete parameters, NB. this config item is added for the sake of performance.
plugin_http_http_params_length_threshold: int = int(
    os.getenv('SW_PLUGIN_HTTP_HTTP_PARAMS_LENGTH_THRESHOLD', '1024'))
# Comma-delimited list of http methods to ignore (GET, POST, HEAD, OPTIONS, etc...)
plugin_http_ignore_method: str = os.getenv('SW_PLUGIN_HTTP_IGNORE_METHOD', '').upper()
# The maximum length of the collected parameter, parameters longer than the specified length will be truncated,
# length 0 turns off parameter tracing
plugin_sql_parameters_max_length: int = int(os.getenv('SW_PLUGIN_SQL_PARAMETERS_MAX_LENGTH', '0'))
# Indicates whether to collect the filters of pymongo
plugin_pymongo_trace_parameters: bool = os.getenv('SW_PLUGIN_PYMONGO_TRACE_PARAMETERS', '').lower() == 'true'
# The maximum length of the collected filters, filters longer than the specified length will be truncated
plugin_pymongo_parameters_max_length: int = int(os.getenv('SW_PLUGIN_PYMONGO_PARAMETERS_MAX_LENGTH', '512'))
# If true, trace all the DSL(Domain Specific Language) in ElasticSearch access, default is false
plugin_elasticsearch_trace_dsl: bool = os.getenv('SW_PLUGIN_ELASTICSEARCH_TRACE_DSL', '').lower() == 'true'
# This config item controls that whether the Flask plugin should collect the parameters of the request.
plugin_flask_collect_http_params: bool = os.getenv('SW_PLUGIN_FLASK_COLLECT_HTTP_PARAMS', '').lower() == 'true'
# This config item controls that whether the Sanic plugin should collect the parameters of the request.
plugin_sanic_collect_http_params: bool = os.getenv('SW_PLUGIN_SANIC_COLLECT_HTTP_PARAMS', '').lower() == 'true'
# This config item controls that whether the Django plugin should collect the parameters of the request.
plugin_django_collect_http_params: bool = os.getenv('SW_PLUGIN_DJANGO_COLLECT_HTTP_PARAMS', '').lower() == 'true'
# This config item controls that whether the FastAPI plugin should collect the parameters of the request.
plugin_fastapi_collect_http_params: bool = os.getenv('SW_PLUGIN_FASTAPI_COLLECT_HTTP_PARAMS', '').lower() == 'true'
# This config item controls that whether the Bottle plugin should collect the parameters of the request.
plugin_bottle_collect_http_params: bool = os.getenv('SW_PLUGIN_BOTTLE_COLLECT_HTTP_PARAMS', '').lower() == 'true'
# The maximum length of `celery` functions parameters, longer than this will be truncated, 0 turns off
plugin_celery_parameters_length: int = int(os.getenv('SW_PLUGIN_CELERY_PARAMETERS_LENGTH', '512'))
# Comma-delimited list of user-defined grpc methods to ignore, like /package.Service/Method1,/package.Service/Method2
plugin_grpc_ignored_methods: str = os.getenv('SW_PLUGIN_GRPC_IGNORED_METHODS', '').upper()

# BEGIN: Sampling Configurations
# The number of samples to take in every 3 seconds, 0 turns off
sample_n_per_3_secs: int = int(os.getenv('SW_SAMPLE_N_PER_3_SECS', '0'))

# THIS MUST FOLLOW DIRECTLY AFTER LIST OF CONFIG OPTIONS!
options = [key for key in globals() if key not in options]  # THIS MUST FOLLOW DIRECTLY AFTER LIST OF CONFIG OPTIONS!

options_with_default_value_and_type = {key: (globals()[key], type(globals()[key])) for key in options}


def init(**kwargs) -> None:
    """
    Used to initialize the configuration of the SkyWalking Python Agent.
    Refer to the official online documentation
    https://skywalking.apache.org/docs/skywalking-python/next/en/setup/configuration/
    for more information on the configuration options.

    Args:
        **kwargs: Any of the configuration options listed
    """
    glob = globals()
    for key, val in kwargs.items():
        if key not in options:
            raise KeyError(f'Invalid configuration option {key}')

        glob[key] = val


def finalize_feature() -> None:
    """
    Examine reporter configuration and warn users about the incompatibility of protocol vs features
    """
    global agent_profile_active, agent_meter_reporter_active

    if agent_protocol == 'http' and (agent_profile_active or agent_meter_reporter_active):
        agent_profile_active = False
        agent_meter_reporter_active = False
        warnings.warn('HTTP protocol does not support meter reporter and profiler. Please use gRPC protocol if you '
                      'would like to use both features.')
    elif agent_protocol == 'kafka' and agent_profile_active:
        agent_profile_active = False
        warnings.warn('Kafka protocol does not support profiler. Please use gRPC protocol if you would like to use '
                      'this feature.')


def finalize_name() -> None:
    """
    This function concatenates the serviceName according to
    Java agent's implementation.
    TODO: add cluster concept
    Ref https://github.com/apache/skywalking-java/pull/123
    """
    global agent_name
    if agent_namespace:
        agent_name = f'{agent_name}|{agent_namespace}'

    global kafka_topic_management, kafka_topic_meter, kafka_topic_log, kafka_topic_segment
    if kafka_namespace:
        kafka_topic_management = f'{kafka_namespace}-{kafka_topic_management}'
        kafka_topic_meter = f'{kafka_namespace}-{kafka_topic_meter}'
        kafka_topic_log = f'{kafka_namespace}-{kafka_topic_log}'
        kafka_topic_segment = f'{kafka_namespace}-{kafka_topic_segment}'


def finalize_regex() -> None:
    """
    Build path matchers based on user provided regex expressions
    """
    reesc = re.compile(r'([.*+?^=!:${}()|\[\]\\])')
    suffix = r'^.+(?:' + '|'.join(reesc.sub(r'\\\1', s.strip()) for s in agent_ignore_suffix.split(',')) + ')$'
    method = r'^' + '|'.join(s.strip() for s in plugin_http_ignore_method.split(',')) + '$'
    grpc_method = r'^' + '|'.join(s.strip() for s in plugin_grpc_ignored_methods.split(',')) + '$'
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
               ) for p0 in agent_trace_ignore_path.split(',')
           ) + ')$'

    global RE_IGNORE_PATH, RE_HTTP_IGNORE_METHOD, RE_GRPC_IGNORED_METHODS
    RE_IGNORE_PATH = re.compile(f'{suffix}|{path}')
    RE_HTTP_IGNORE_METHOD = re.compile(method, re.IGNORECASE)
    RE_GRPC_IGNORED_METHODS = re.compile(grpc_method, re.IGNORECASE)


def ignore_http_method_check(method: str):
    return RE_HTTP_IGNORE_METHOD.match(method)


def ignore_grpc_method_check(method: str):
    return RE_GRPC_IGNORED_METHODS.match(method)


def finalize() -> None:
    """
    invokes finalizers
    """
    finalize_feature()
    finalize_regex()
    finalize_name()
