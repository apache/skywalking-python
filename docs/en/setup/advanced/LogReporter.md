# Python Agent Log Reporter

This functionality reports logs collected from the Python logging module (in theory, also logging libraries depending on the core logging module) and loguru module.

From Python agent 1.0.0, the log reporter is automatically enabled and can be disabled through `agent_log_reporter_active=False` or `SW_AGENT_LOG_REPORTER_ACTIVE=False`.

Log reporter supports all three protocols including `grpc`, `http` and `kafka`, which shares the same config `agent_protocol` with trace reporter.

If chosen `http` protocol, the logs will be batch-reported to the collector REST endpoint `oap/v3/logs`.

If chosen `kafka` protocol, please make sure to config 
[kafka-fetcher](https://skywalking.apache.org/docs/main/v9.1.0/en/setup/backend/kafka-fetcher/) 
on the OAP side, and make sure Python agent config `kafka_bootstrap_servers` points to your Kafka brokers.

**Please make sure OAP is consuming the same Kafka topic as your agent produces to, `kafka_namespace` must match OAP side configuration `plugin.kafka.namespace`**

`agent_log_reporter_active=True` - Enables the log reporter.

`agent_log_reporter_max_buffer_size` - The maximum queue backlog size for sending log data to backend, logs beyond this are silently dropped.

Alternatively, you can pass configurations through environment variables. 
Please refer to the [Configuration Vocabulary](../Configuration.md) for the list of environment variables associated with the log reporter.

## Specify a logging level
> [Important] Agent will only report logs that passes the default level threshold logging.getLogger().setLevel(logging.WARNING) 
> For example, if your logger level is logging.INFO, agent will not report info logs even if you set `agent_log_reporter_level` to `INFO`

Additional to the code level configuration, only the logs with a level equal to or higher than the 
specified configuration will be collected and reported. 

In other words, the agent skips reporting some unwanted logs based on your level threshold even though they are still logged.

`log_reporter_level` - The string name of a logger level. 

Note that it also works with your custom logger levels, simply specify its string name in the config.

### Ignore log filters
The following config is disabled by default. When enabled, the log reporter will collect logs disregarding your custom log filters.

For example, if you attach the filter below to the logger - the default behavior of log reporting aligns with the filter 
(not reporting any logs with a message starting with `SW test`)
```python
class AppFilter(logging.Filter):
    def filter(self, record):
        return not record.getMessage().startswith('SW test')

logger.addFilter(AppFilter())
```
However, if you do would like to report those filtered logs, set the `log_reporter_ignore_filter` to `True`.


## Formatting
Note that regardless of the formatting, Python agent will always report the following three tags - 

`level` - the logger level name

`logger` - the logger name  

`thread` - the thread name

### Limit stacktrace depth
You can set the `cause_exception_depth` config entry to a desired level(defaults to 10), which limits the output depth of exception stacktrace in reporting.

This config limits agent to report up to `limit` stacktrace, please refer to [Python traceback](https://docs.python.org/3/library/traceback.html#traceback.print_tb) for more explanations.

### Customize the reported log format
You can choose to report collected logs in a custom layout.

If not set, the agent uses the layout below by default, else the agent uses your custom layout set in `log_reporter_layout`.

`'%(asctime)s [%(threadName)s] %(levelname)s %(name)s - %(message)s'`

If the layout is set to `None`, the reported log content will only contain 
the pre-formatted `LogRecord.message`(`msg % args`) without any additional styles or extra fields, stacktrace will be attached if an exception was raised. 

### Transmit un-formatted logs
You can also choose to report the log messages without any formatting.
It separates the raw log msg `logRecord.msg` and `logRecord.args`, then puts them into message content and tags starting from `argument.0`, respectively, along with an `exception` tag if an exception was raised.

Note when you set `log_reporter_formatted` to False, it ignores your custom layout introduced above.

As an example, the following code:
```python
logger.info("SW test log %s %s %s", 'arg0', 'arg1', 'arg2')
```

Will result in:
```json
{
  "content": "SW test log %s %s %s",
  "tags": [
    {
      "key": "argument.0",
      "value": "arg0"
    },
    {
      "key": "argument.1",
      "value": "arg1"
    },
    {
      "key": "argument.2",
      "value": "arg2"
    }
  ]
}
```