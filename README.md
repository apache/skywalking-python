# SkyWalking Python Agent

<img src="http://skywalking.apache.org/assets/logo.svg" alt="Sky Walking logo" height="90px" align="right" />

**SkyWalking-Python**: The Python Agent for Apache SkyWalking, which provides the native tracing abilities for Python project.

**SkyWalking**: an APM(application performance monitor) system, especially designed for
microservices, cloud native and container-based (Docker, Kubernetes, Mesos) architectures.

[![GitHub stars](https://img.shields.io/github/stars/apache/skywalking-python.svg?style=for-the-badge&label=Stars&logo=github)](https://github.com/apache/skywalking-python)
[![Twitter Follow](https://img.shields.io/twitter/follow/asfskywalking.svg?style=for-the-badge&label=Follow&logo=twitter)](https://twitter.com/AsfSkyWalking)

[![Build](https://github.com/apache/skywalking-python/workflows/Build/badge.svg?branch=master)](https://github.com/apache/skywalking-python/actions?query=branch%3Amaster+event%3Apush+workflow%3A%22Build%22)

## Documentation

- [Official documentation](https://skywalking.apache.org/docs/#PythonAgent)
- [Blog](https://skywalking.apache.org/blog/2021-09-12-skywalking-python-profiling/) about the Python Agent Profiling Feature

## Installation Requirements

SkyWalking Python Agent requires SkyWalking 8.0+ and Python 3.6+.

> If you would like to try out the latest features that are not released yet, please refer to this [guide](docs/en/setup/faq/How-to-build-from-sources.md) to build from sources.

## Contributing

Before submitting a pull request or pushing a commit, please read our [contributing](CONTRIBUTING.md) and [developer guide](docs/en/contribution/Developer.md).

## Contact Us
* Submit an [GitHub Issue](https://github.com/apache/skywalking/issues/new) by using [Python] as title prefix.
* Mail list: **dev@skywalking.apache.org**. Mail to `dev-subscribe@skywalking.apache.org`, follow the reply to subscribe the mail list.
* Join `skywalking` channel at [Apache Slack](http://s.apache.org/slack-invite). If the link is not working, find the latest one at [Apache INFRA WIKI](https://cwiki.apache.org/confluence/display/INFRA/Slack+Guest+Invites).
* Twitter, [ASFSkyWalking](https://twitter.com/AsfSkyWalking)

## License
Apache 2.0


key concept:
ProfileTaskExecutionService
ProfileTaskExecutionContext
ProfileThread
ThreadProfiler

服务启动后，定时轮询oap，发现新的profiling task
一旦有新的profiling task,则：
ProfileTaskCommandExecutor执行 profile_task_execution_service.add_profile_task()
时间到后，执行service.process_profile_task(),通过context.start_profiling()启动profiling,同时设置定时器，task到期后执行service.stop_current_profile_task()关闭profiling

context.start_profiling时，创建一个ProfileThread(taskContext)，这个线程会不停dump taskThread出来，如果dump成功，则会发一个snapshot到OAP.profile的逻辑在ProfileThread实现


改为Greenlet模式后，start_profiling()就应该settrace() callback， 不再需要另外起一个线程


context.new_entry_span(),判断是否有profile，如果有，则通过profile_task_execution_service.add_profiling()向ProfileSlot增加一个profiling,ProfileThread在轮询ProfileSlot，发现新增的ProfileSlot则自动执行Profiler.profiling()

# greenlet的profiler会在创建时自动启动，而threadmode的profiler需要在另外的ProfileThread运行