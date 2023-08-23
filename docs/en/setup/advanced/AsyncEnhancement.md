# Python Agent Asynchronous Enhancement

Since `1.1.0`, the Python agent supports asynchronous reporting of ALL telemetry data, including traces, metrics, logs and profile. This feature is disabled by default, since it is still in the experimental stage. You can enable it by setting the `SW_AGENT_ASYNCIO_ENHANCEMENT` environment variable to `true`. See [the configuration document](../Configuration.md) for more information.

```bash
export SW_AGENT_ASYNCIO_ENHANCEMENT=true
```

## Why we need this feature

Before version `1.1.0`, SkyWalking Python agent had only an implementation with the Threading module to provide data reporters. Yet with the growth of the Python agent, it is now fully capable and requires more resources than when only tracing was supported (we start many threads and gRPC itself creates even more threads when streaming).

As well known, the Global Interpreter Lock (GIL) in Python can limit the true parallel execution of threads. This issue also effects the Python agent, especially on network communication with the SkyWalking OAP (gRPC, HTTP and Kafka).

Therefore, we have decided to implement the reporter code for the SkyWalking Python agent based on the `asyncio` library. `asyncio` is an officially supported asynchronous programming library in Python that operates on a single-threaded, coroutine-driven model. Currently, it enjoys widespread adoption and boasts a rich ecosystem, making it the preferred choice for enhancing asynchronous capabilities in many Python projects.

## How it works

To keep the API unchanged, we have completely rewritten a new class called `SkyWalkingAgentAsync` (identical to the `SkyWalkingAgent` class). We use the environment variable mentioned above, `SW_AGENT_ASYNCIO_ENHANCEMENT`, to control which class implements the agent's interface.

In the `SkyWalkingAgentAsync` class, we have employed asyncio coroutines and their related functions to replace the Python threading implementation in nearly all instances. And we have applied asyncio enhancements to all three primary reporting protocols of the current SkyWalking Python agent:

- **gRPC**: We use the [`grpc.aio`](https://grpc.github.io/grpc/python/grpc_asyncio.html) module to replace the `grpc` module. Since the `grpc.aio` module is also officially supported and included in the `grpc` package, we can use it directly without any additional installation.

- **HTTP**: We use the [`aiohttp`](https://github.com/aio-libs/aiohttp) module to replace the `requests` module.

- **Kafka**: We use the [`aiokafka`](https://github.com/aio-libs/aiokafka) module to replace the `kafka-python` module.

## Performance improvement

We use [wrk](https://github.com/wg/wrk) to pressure test the network throughput of the Python agents in a [FastAPI](https://github.com/tiangolo/fastapi) application.

- gRPC

The performance has been improved by about **32.8%**

|      gRPC       |   QPS   |   TPS    | Avg Latency |
| :-------------: | :-----: | :------: | :---------: |
| sync (original) | 899.26  | 146.66KB |  545.97ms   |
|   async (new)   | 1194.55 | 194.81KB |  410.97ms   |

- HTTP

The performance has been improved by about **9.8%**

|      HTTP       |  QPS   |   TPS   | Avg Latency |
| :-------------: | :----: | :-----: | :---------: |
| sync (original) | 530.95 | 86.59KB |    1.53s    |
|   async (new)   | 583.37 | 95.14KB |    1.44s    |

- Kafka

The performance has been improved by about **89.6%**

|      Kafka      |  QPS   |   TPS    | Avg Latency |
| :-------------: | :----: | :------: | :---------: |
| sync (original) | 345.89 | 56.41KB  |    1.09s    |
|   async (new)   | 655.67 | 106.93KB |    1.24s    |

> In fact, only the performance improvement of gRPC is of more reference value. Because the other two protocols use third-party libraries with completely different implementations, the performance improvement depends to a certain extent on the performance of these third-party libraries.

More details see this [PR](https://github.com/apache/skywalking-python/pull/316) .

## Potential problems

We have shown that the asynchronous enhancement function improves the transmission efficiency of metrics, traces and logs. But **it improves the proformance of profile data very little, and even causes performance degradation**.

This is mainly because a large part of the data in the `profile` part comes from the monitoring and measurement of Python threads, which is exactly what we need to avoid in asynchronous enhancement. Since operations on threads cannot be bypassed, we may need additional overhead to support cross-thread coroutine communication, which may lead to performance degradation instead of increase.

Asynchronous enhancements involve many code changes and introduced some new dependencies. Since this feature is relatively new, it may cause some unexpected errors and problems. **If you encounter them, please feel free to contact us or submit issues and PRs**!
