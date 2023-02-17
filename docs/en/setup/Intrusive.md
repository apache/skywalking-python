# Legacy Setup

You can always fall back to our traditional way of integration as introduced below, 
which is by importing SkyWalking into your project and starting the agent.

## Defaults
By default, SkyWalking Python agent uses gRPC protocol to report data to SkyWalking backend,
in SkyWalking backend, the port of gRPC protocol is `11800`, and the port of HTTP protocol is `12800`,

See all default configuration values in the [Configuration Vocabulary](Configuration.md)

You could configure `agent_collector_backend_services` (or environment variable `SW_AGENT_COLLECTOR_BACKEND_SERVICES`)
and set `agent_protocol` (or environment variable `SW_AGENT_PROTOCOL` to one of
`gprc`, `http` or `kafka` according to the protocol you would like to use.

### Report data via gRPC protocol (Default)

For example, if you want to use gRPC protocol to report data, configure `agent_collector_backend_services`
(or environment variable `SW_AGENT_COLLECTOR_BACKEND_SERVICES`) to `<oap-ip-or-host>:11800`,
such as `127.0.0.1:11800`:

```python
from skywalking import agent, config

config.init(agent_collector_backend_services='127.0.0.1:11800', agent_name='your awesome service', agent_instance_name='your-instance-name or <generated uuid>')

agent.start()
```

### Report data via HTTP protocol

However, if you want to use HTTP protocol to report data, configure `agent_collector_backend_services`
(or environment variable `SW_AGENT_COLLECTOR_BACKEND_SERVICES`) to `<oap-ip-or-host>:12800`,
such as `127.0.0.1:12800`, further set `agent_protocol` (or environment variable `SW_AGENT_PROTOCOL` to `http`):

> Remember you should install `skywalking-python` with extra requires `http`, `pip install "apache-skywalking[http]`.

```python
from skywalking import agent, config

config.init(agent_collector_backend_services='127.0.0.1:12800', agent_name='your awesome service', agent_protocol='http', agent_instance_name='your-instance-name or <generated uuid>')

agent.start()
```

### Report data via Kafka protocol
**Please make sure OAP is consuming the same Kafka topic as your agent produces to, `kafka_namespace` must match OAP side configuration `plugin.kafka.namespace`**

Finally, if you want to use Kafka protocol to report data, configure `kafka_bootstrap_servers`
(or environment variable `SW_KAFKA_BOOTSTRAP_SERVERS`) to `kafka-brokers`,
such as `127.0.0.1:9200`, further set `agent_protocol` (or environment variable `SW_AGENT_PROTOCOL` to `kafka`):

> Remember you should install `skywalking-python` with extra requires `kafka`, `pip install "apache-skywalking[kafka]"`.

```python
from skywalking import agent, config

config.init(kafka_bootstrap_servers='127.0.0.1:9200', agent_name='your awesome service', agent_protocol='kafka', agent_instance_name='your-instance-name or <generated uuid>')

agent.start()
```

Alternatively, you can also pass the configurations via environment variables (such as `SW_AGENT_NAME`, `SW_AGENT_COLLECTOR_BACKEND_SERVICES`, etc.) so that you don't need to call `config.init`.

All supported environment variables can be found in the [Environment Variables List](Configuration.md).
