# Supported Agent Configuration Options

Below is the full list of supported configurations you can set to
customize the agent behavior, please take some time to read the descriptions for what they can achieve.

> Usage: (Pass in intrusive setup)
```
from skywalking import config, agent
config.init(YourConfiguration=YourValue))
agent.start()
```
> Usage: (Pass by environment variables)
```
export SW_AGENT_YourConfiguration=YourValue
```

###  Agent Core Configuration Options
| Configuration | Environment Variable | Type | Default Value | Description |
| :------------ | :------------ | :------------ | :------------ | :------------ |
| agent_collector_backend_services | SW_AGENT_COLLECTOR_BACKEND_SERVICES | <class 'str'> | oap_host:oap_port | The backend OAP server address, 11800 is default OAP gRPC port, 12800 is HTTP, Kafka ignores this option and uses kafka_bootstrap_servers option. **This option should be changed accordingly with selected protocol** |
| agent_protocol | SW_AGENT_PROTOCOL | <class 'str'> | grpc | The protocol to communicate with the backend OAP, `http`, `grpc` or `kafka`, **we highly suggest using `grpc` in production as it's well optimized than `http`**. The `kafka` protocol provides an alternative way to submit data to the backend. |
| agent_name | SW_AGENT_NAME | <class 'str'> | Python Service Name | The name of your awesome Python service |
| agent_instance_name | SW_AGENT_INSTANCE_NAME | <class 'str'> | str(uuid.uuid1()).replace('-', '') | The name of this particular awesome Python service instance |
| agent_namespace | SW_AGENT_NAMESPACE | <class 'str'> |  | The agent namespace of the Python service (available as tag and the suffix of service name) |
| kafka_bootstrap_servers | SW_KAFKA_BOOTSTRAP_SERVERS | <class 'str'> | localhost:9092 | A list of host/port pairs to use for establishing the initial connection to your Kafka cluster. It is in the form of host1:port1,host2:port2,... (used for Kafka reporter protocol) |
| kafka_namespace | SW_KAFKA_NAMESPACE | <class 'str'> |  | The kafka namespace specified by OAP side SW_NAMESPACE, prepends the following kafka topic names with a `-`. |
| kafka_topic_management | SW_KAFKA_TOPIC_MANAGEMENT | <class 'str'> | skywalking-managements | Specifying Kafka topic name for service instance reporting and registering, this should be in sync with OAP |
| kafka_topic_segment | SW_KAFKA_TOPIC_SEGMENT | <class 'str'> | skywalking-segments | Specifying Kafka topic name for Tracing data, this should be in sync with OAP |
| kafka_topic_log | SW_KAFKA_TOPIC_LOG | <class 'str'> | skywalking-logs | Specifying Kafka topic name for Log data, this should be in sync with OAP |
| kafka_topic_meter | SW_KAFKA_TOPIC_METER | <class 'str'> | skywalking-meters | Specifying Kafka topic name for Meter data, this should be in sync with OAP |
| kafka_reporter_custom_configurations | SW_KAFKA_REPORTER_CUSTOM_CONFIGURATIONS | <class 'str'> |  | The configs to init KafkaProducer, supports the basic arguments (whose type is either `str`, `bool`, or `int`) listed [here](https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html#kafka.KafkaProducer) This config only works from env variables, each one should be passed in `SW_KAFKA_REPORTER_CONFIG_<KEY_NAME>` |
| agent_force_tls | SW_AGENT_FORCE_TLS | <class 'bool'> | False | Use TLS for communication with SkyWalking OAP (no cert required) |
| agent_authentication | SW_AGENT_AUTHENTICATION | <class 'str'> |  | The authentication token to verify that the agent is trusted by the backend OAP, as for how to configure the backend, refer to [the yaml](https://github.com/apache/skywalking/blob/4f0f39ffccdc9b41049903cc540b8904f7c9728e/oap-server/server-bootstrap/src/main/resources/application.yml#L155-L158). |
| agent_logging_level | SW_AGENT_LOGGING_LEVEL | <class 'str'> | INFO | The level of agent self-logs, could be one of `CRITICAL`, `FATAL`, `ERROR`, `WARN`(`WARNING`), `INFO`, `DEBUG`. Please turn on debug if an issue is encountered to find out what's going on |
###  Agent Core Danger Zone
| Configuration | Environment Variable | Type | Default Value | Description |
| :------------ | :------------ | :------------ | :------------ | :------------ |
| agent_collector_heartbeat_period | SW_AGENT_COLLECTOR_HEARTBEAT_PERIOD | <class 'int'> | 30 | The agent will exchange heartbeat message with SkyWalking OAP backend every `period` seconds |
| agent_collector_properties_report_period_factor | SW_AGENT_COLLECTOR_PROPERTIES_REPORT_PERIOD_FACTOR | <class 'int'> | 10 | The agent will report service instance properties every `factor * heartbeat period` seconds default: 10*30 = 300 seconds |
| agent_instance_properties_json | SW_AGENT_INSTANCE_PROPERTIES_JSON | <class 'str'> |  | A custom JSON string to be reported as service instance properties, e.g. `{"key": "value"}` |
| agent_experimental_fork_support | SW_AGENT_EXPERIMENTAL_FORK_SUPPORT | <class 'bool'> | False | The agent will restart itself in any os.fork()-ed child process. Important Note: it's not suitable for short-lived processes as each one will create a new instance in SkyWalking dashboard in format of `service_instance-child(pid)`. This feature may not work when a precise combination of gRPC + Python 3.7 + subprocess (not fork) is used together. The agent will output a warning log when using on Python 3.7 for such a reason. |
| agent_queue_timeout | SW_AGENT_QUEUE_TIMEOUT | <class 'int'> | 1 | DANGEROUS - This option controls the interval of each bulk report from telemetry data queues Do not modify unless you have evaluated its impact given your service load. |
###  SW_PYTHON Auto Instrumentation CLI
| Configuration | Environment Variable | Type | Default Value | Description |
| :------------ | :------------ | :------------ | :------------ | :------------ |
| agent_sw_python_bootstrap_propagate | SW_AGENT_SW_PYTHON_BOOTSTRAP_PROPAGATE | <class 'bool'> | False | Special: can only be passed via environment. This config controls the child process agent bootstrap behavior in `sw-python` CLI, if set to `False`, a valid child process will not boot up a SkyWalking Agent. Please refer to the [CLI Guide](CLI.md) for details. |
| agent_sw_python_cli_debug_enabled | SW_AGENT_SW_PYTHON_CLI_DEBUG_ENABLED | <class 'bool'> | False | Special: can only be passed via environment. This config controls the CLI and agent logging debug mode, if set to `True`, the CLI and agent will print out debug logs. Please refer to the [CLI Guide](CLI.md) for details. Important: this config will set agent logging level to `DEBUG` as well, do not use it in production otherwise it will flood your logs. This normally shouldn't be pass as a simple flag -d will be the same. |
###  Trace Reporter Configurations
| Configuration | Environment Variable | Type | Default Value | Description |
| :------------ | :------------ | :------------ | :------------ | :------------ |
| agent_trace_reporter_max_buffer_size | SW_AGENT_TRACE_REPORTER_MAX_BUFFER_SIZE | <class 'int'> | 10000 | The maximum queue backlog size for sending the segment data to backend, segments beyond this are silently dropped |
| agent_trace_ignore_path | SW_AGENT_TRACE_IGNORE_PATH | <class 'str'> |  | You can setup multiple URL path patterns, The endpoints match these patterns wouldn't be traced. the current matching rules follow Ant Path match style , like /path/*, /path/**, /path/?. |
| agent_ignore_suffix | SW_AGENT_IGNORE_SUFFIX | <class 'str'> | .jpg,.jpeg,.js,.css,.png,.bmp,.gif,.ico,.mp3,.mp4,.html,.svg  | If the operation name of the first span is included in this set, this segment should be ignored. |
| correlation_element_max_number | SW_CORRELATION_ELEMENT_MAX_NUMBER | <class 'int'> | 3 | Max element count of the correlation context. |
| correlation_value_max_length | SW_CORRELATION_VALUE_MAX_LENGTH | <class 'int'> | 128 | Max value length of correlation context element. |
###  Profiling Configurations
| Configuration | Environment Variable | Type | Default Value | Description |
| :------------ | :------------ | :------------ | :------------ | :------------ |
| agent_profile_active | SW_AGENT_PROFILE_ACTIVE | <class 'bool'> | True | If `True`, Python agent will enable profiler when user create a new profiling task. |
| agent_collector_get_profile_task_interval | SW_AGENT_COLLECTOR_GET_PROFILE_TASK_INTERVAL | <class 'int'> | 20 | The number of seconds between two profile task query. |
| agent_profile_max_parallel | SW_AGENT_PROFILE_MAX_PARALLEL | <class 'int'> | 5 | The number of parallel monitor segment count. |
| agent_profile_duration | SW_AGENT_PROFILE_DURATION | <class 'int'> | 10 | The maximum monitor segment time(minutes), if current segment monitor time out of limit, then stop it. |
| agent_profile_dump_max_stack_depth | SW_AGENT_PROFILE_DUMP_MAX_STACK_DEPTH | <class 'int'> | 500 | The number of max dump thread stack depth |
| agent_profile_snapshot_transport_buffer_size | SW_AGENT_PROFILE_SNAPSHOT_TRANSPORT_BUFFER_SIZE | <class 'int'> | 50 | The number of snapshot transport to backend buffer size |
###  Log Reporter Configurations
| Configuration | Environment Variable | Type | Default Value | Description |
| :------------ | :------------ | :------------ | :------------ | :------------ |
| agent_log_reporter_active | SW_AGENT_LOG_REPORTER_ACTIVE | <class 'bool'> | True | If `True`, Python agent will report collected logs to the OAP or Satellite. Otherwise, it disables the feature. |
| agent_log_reporter_safe_mode | SW_AGENT_LOG_REPORTER_SAFE_MODE | <class 'bool'> | False | If `True`, Python agent will filter out HTTP basic auth information from log records. By default, it disables the feature due to potential performance impact brought by regular expression |
| agent_log_reporter_max_buffer_size | SW_AGENT_LOG_REPORTER_MAX_BUFFER_SIZE | <class 'int'> | 10000 | The maximum queue backlog size for sending log data to backend, logs beyond this are silently dropped. |
| agent_log_reporter_level | SW_AGENT_LOG_REPORTER_LEVEL | <class 'str'> | WARNING | This config specifies the logger levels of concern, any logs with a level below the config will be ignored. |
| agent_log_reporter_ignore_filter | SW_AGENT_LOG_REPORTER_IGNORE_FILTER | <class 'bool'> | False | This config customizes whether to ignore the application-defined logger filters, if `True`, all logs are reported disregarding any filter rules. |
| agent_log_reporter_formatted | SW_AGENT_LOG_REPORTER_FORMATTED | <class 'bool'> | True | If `True`, the log reporter will transmit the logs as formatted. Otherwise, puts logRecord.msg and logRecord.args into message content and tags(`argument.n`), respectively. Along with an `exception` tag if an exception was raised. Only applies to logging module. |
| agent_log_reporter_layout | SW_AGENT_LOG_REPORTER_LAYOUT | <class 'str'> | %(asctime)s [%(threadName)s] %(levelname)s %(name)s - %(message)s | The log reporter formats the logRecord message based on the layout given. Only applies to logging module. |
| agent_cause_exception_depth | SW_AGENT_CAUSE_EXCEPTION_DEPTH | <class 'int'> | 10 | This configuration is shared by log reporter and tracer. This config limits agent to report up to `limit` stacktrace, please refer to [Python traceback]( https://docs.python.org/3/library/traceback.html#traceback.print_tb) for more explanations. |
###  Meter Reporter Configurations
| Configuration | Environment Variable | Type | Default Value | Description |
| :------------ | :------------ | :------------ | :------------ | :------------ |
| agent_meter_reporter_active | SW_AGENT_METER_REPORTER_ACTIVE | <class 'bool'> | True | If `True`, Python agent will report collected meters to the OAP or Satellite. Otherwise, it disables the feature. |
| agent_meter_reporter_max_buffer_size | SW_AGENT_METER_REPORTER_MAX_BUFFER_SIZE | <class 'int'> | 10000 | The maximum queue backlog size for sending meter data to backend, meters beyond this are silently dropped. |
| agent_meter_reporter_period | SW_AGENT_METER_REPORTER_PERIOD | <class 'int'> | 20 | The interval in seconds between each meter data report |
| agent_pvm_meter_reporter_active | SW_AGENT_PVM_METER_REPORTER_ACTIVE | <class 'bool'> | True | If `True`, Python agent will report collected Python Virtual Machine (PVM) meters to the OAP or Satellite. Otherwise, it disables the feature. |
###  Plugin Related configurations
| Configuration | Environment Variable | Type | Default Value | Description |
| :------------ | :------------ | :------------ | :------------ | :------------ |
| agent_disable_plugins | SW_AGENT_DISABLE_PLUGINS | <class 'list'> | [''] | The name patterns in comma-separated pattern, plugins whose name matches one of the pattern won't be installed |
| plugin_http_http_params_length_threshold | SW_PLUGIN_HTTP_HTTP_PARAMS_LENGTH_THRESHOLD | <class 'int'> | 1024 | When `COLLECT_HTTP_PARAMS` is enabled, how many characters to keep and send to the OAP backend, use negative values to keep and send the complete parameters, NB. this config item is added for the sake of performance. |
| plugin_http_ignore_method | SW_PLUGIN_HTTP_IGNORE_METHOD | <class 'str'> |  | Comma-delimited list of http methods to ignore (GET, POST, HEAD, OPTIONS, etc...) |
| plugin_sql_parameters_max_length | SW_PLUGIN_SQL_PARAMETERS_MAX_LENGTH | <class 'int'> | 0 | The maximum length of the collected parameter, parameters longer than the specified length will be truncated, length 0 turns off parameter tracing |
| plugin_pymongo_trace_parameters | SW_PLUGIN_PYMONGO_TRACE_PARAMETERS | <class 'bool'> | False | Indicates whether to collect the filters of pymongo |
| plugin_pymongo_parameters_max_length | SW_PLUGIN_PYMONGO_PARAMETERS_MAX_LENGTH | <class 'int'> | 512 | The maximum length of the collected filters, filters longer than the specified length will be truncated |
| plugin_elasticsearch_trace_dsl | SW_PLUGIN_ELASTICSEARCH_TRACE_DSL | <class 'bool'> | False | If true, trace all the DSL(Domain Specific Language) in ElasticSearch access, default is false |
| plugin_flask_collect_http_params | SW_PLUGIN_FLASK_COLLECT_HTTP_PARAMS | <class 'bool'> | False | This config item controls that whether the Flask plugin should collect the parameters of the request. |
| plugin_sanic_collect_http_params | SW_PLUGIN_SANIC_COLLECT_HTTP_PARAMS | <class 'bool'> | False | This config item controls that whether the Sanic plugin should collect the parameters of the request. |
| plugin_django_collect_http_params | SW_PLUGIN_DJANGO_COLLECT_HTTP_PARAMS | <class 'bool'> | False | This config item controls that whether the Django plugin should collect the parameters of the request. |
| plugin_fastapi_collect_http_params | SW_PLUGIN_FASTAPI_COLLECT_HTTP_PARAMS | <class 'bool'> | False | This config item controls that whether the FastAPI plugin should collect the parameters of the request. |
| plugin_bottle_collect_http_params | SW_PLUGIN_BOTTLE_COLLECT_HTTP_PARAMS | <class 'bool'> | False | This config item controls that whether the Bottle plugin should collect the parameters of the request. |
| plugin_celery_parameters_length | SW_PLUGIN_CELERY_PARAMETERS_LENGTH | <class 'int'> | 512 | The maximum length of `celery` functions parameters, longer than this will be truncated, 0 turns off |
