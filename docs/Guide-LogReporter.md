# Python agent gRPC log reporter

This functionality reports logs collected from the Python logging module(in theory, also logging libraries depending on the core logging module).

To utilize this feature, you will need to add some new configurations to the agent initialization step.

## Enabling the feature
```Python 
from skywalking import agent, config

config.init(collector_address='127.0.0.1:11800', service_name='your awesome service',
                log_grpc_reporter_active=True, log_grpc_collector_address='127.0.0.1:11800')
agent.start()
``` 

`log_grpc_reporter_active=True` - Enables the log reporter.

`log_grpc_collector_address` - For now, the log reporter uses a separate gRPC channel(will be merged upon the [SkyWalking-Satellite](https://github.com/apache/skywalking-satellite) project matures). 
If you would like to use [SkyWalking-Satellite](https://github.com/apache/skywalking-satellite), you will need to configure an address pointing to the Satellite. Otherwise, you can simply keep the address the same as the OAP.

`log_grpc_reporter_max_buffer_size` and  `log_grpc_reporter_max_message_size` - Used to limit the reporting overhead.

Alternatively, you can pass configurations through environment variables. 
Please refer to [EnvVars.md](EnvVars.md) for the list of environment variables associated with the log reporter.

## Specify a logging level
Only the logs with a level equal to or higher than the specified will be collected and reported. 
In other words, the agent ignores some unwanted logs based on your level threshold.

`log_grpc_reporter_level` - The string name of a logger level. 

Note that it also works with your custom logger levels, simply specify its string name in the config.

## Formatting
Note that regardless of the formatting, Python agent will always report the following three tags - 

`level` - the logger level name

`logger` - the logger name  

`thread` - the thread name
### Customize the reported log format
You can choose to report collected logs in a custom layout.

If not set, the agent uses the layout below by default, else the agent uses your custom layout set in `log_grpc_reporter_layout`.

`'%(asctime)s [%(threadName)s] %(levelname)s %(name)s - %(message)s'`

If the layout is set to `None`, the reported log content will only contain the pre-formatted `LogRecord.message`(`msg % args`) without any additional styles and information.

### Transmit un-formatted logs
You can also choose to report the log messages without any formatting.
It separates the raw log msg `logRecord.msg` and `logRecord.args`, then puts them into message content and tags starting from `argument.0`, respectively, along with an `exception` tag if an exception was raised.

Note when you set `log_grpc_reporter_formatted` to False, it ignores your custom layout introduced above.

As an example, the following code:
```Python
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