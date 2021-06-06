# Supported Environment Variables

Environment Variable | Description | Default
| :--- | :--- | :--- |
| `SW_AGENT_NAME` | The name of the Python service | `Python Service Name` |
| `SW_AGENT_INSTANCE` | The name of the Python service instance | Randomly generated |
| `SW_AGENT_COLLECTOR_BACKEND_SERVICES` | The backend OAP server address | `127.0.0.1:11800` |
| `SW_AGENT_PROTOCOL` | The protocol to communicate with the backend OAP, `http`, `grpc` or `kafka`, **we highly suggest using `grpc` in production as it's well optimized than `http`**. The `kafka` protocol provides an alternative way to submit data to the backend. | `grpc` |
| `SW_AGENT_AUTHENTICATION` | The authentication token to verify that the agent is trusted by the backend OAP, as for how to configure the backend, refer to [the yaml](https://github.com/apache/skywalking/blob/4f0f39ffccdc9b41049903cc540b8904f7c9728e/oap-server/server-bootstrap/src/main/resources/application.yml#L155-L158). | unset |
| `SW_AGENT_LOGGING_LEVEL` | The logging level, could be one of `CRITICAL`, `FATAL`, `ERROR`, `WARN`(`WARNING`), `INFO`, `DEBUG` | `INFO` |
| `SW_AGENT_DISABLE_PLUGINS` | The name patterns in CSV pattern, plugins whose name matches one of the pattern won't be installed | `''` |
| `SW_SQL_PARAMETERS_LENGTH` | The maximum length of the collected parameter, parameters longer than the specified length will be truncated, length 0 turns off parameter tracing | `0` |
| `SW_PYMONGO_TRACE_PARAMETERS` | Indicates whether to collect the filters of pymongo | `False` |
| `SW_PYMONGO_PARAMETERS_MAX_LENGTH` | The maximum length of the collected filters, filters longer than the specified length will be truncated |  `512` |
| `SW_IGNORE_SUFFIX` | If the operation name of the first span is included in this set, this segment should be ignored. | `.jpg,.jpeg,.js,.css,.png,.bmp,.gif,.ico,.mp3,.mp4,.html,.svg` |
| `SW_FLASK_COLLECT_HTTP_PARAMS`| This config item controls that whether the Flask plugin should collect the parameters of the request.| `false` |
| `SW_DJANGO_COLLECT_HTTP_PARAMS`| This config item controls that whether the Django plugin should collect the parameters of the request.| `false` |
| `SW_HTTP_PARAMS_LENGTH_THRESHOLD`| When `COLLECT_HTTP_PARAMS` is enabled, how many characters to keep and send to the OAP backend, use negative values to keep and send the complete parameters, NB. this config item is added for the sake of performance.  | `1024` |
| `SW_CORRELATION_ELEMENT_MAX_NUMBER`|Max element count of the correlation context.| `3` |
| `SW_CORRELATION_VALUE_MAX_LENGTH`| Max value length of correlation context element.| `128` |
| `SW_TRACE_IGNORE`| This config item controls that whether the trace should be ignore | `false` |
| `SW_TRACE_IGNORE_PATH`| You can setup multiple URL path patterns, The endpoints match these patterns wouldn't be traced. the current matching rules follow Ant Path match style , like /path/*, /path/**, /path/?.| `''` |
| `SW_ELASTICSEARCH_TRACE_DSL`| If true, trace all the DSL(Domain Specific Language) in ElasticSearch access, default is false | `false` |
| `SW_KAFKA_REPORTER_BOOTSTRAP_SERVERS` | A list of host/port pairs to use for establishing the initial connection to the Kafka cluster. It is in the form host1:port1,host2:port2,... | `localhost:9092` |
| `SW_KAFKA_REPORTER_TOPIC_MANAGEMENT` | Specifying Kafka topic name for service instance reporting and registering. | `skywalking-managements` |
| `SW_KAFKA_REPORTER_TOPIC_SEGMENT` | Specifying Kafka topic name for Tracing data. | `skywalking-segments` |
| `SW_KAFKA_REPORTER_CONFIG_key` | The configs to init KafkaProducer. it support the basic arguments (whose type is either `str`, `bool`, or `int`) listed [here](https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html#kafka.KafkaProducer) | unset |
