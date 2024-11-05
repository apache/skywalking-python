# SkyWalking Python Agent

<img src="http://skywalking.apache.org/assets/logo.svg" alt="Sky Walking logo" height="90px" align="right" />

**SkyWalking-Python**: The Python Agent for Apache SkyWalking provides the native tracing/metrics/logging/profiling abilities for Python projects.

**[SkyWalking](https://github.com/apache/skywalking)**: Application performance monitor tool for distributed systems, especially designed for microservices, cloud native and container-based (Kubernetes) architectures.


[![GitHub stars](https://img.shields.io/github/stars/apache/skywalking-python.svg?style=for-the-badge&label=Stars&logo=github)](https://github.com/apache/skywalking-python)
[![Twitter Follow](https://img.shields.io/twitter/follow/asfskywalking.svg?style=for-the-badge&label=Follow&logo=twitter)](https://twitter.com/AsfSkyWalking)

![Release](https://img.shields.io/pypi/v/apache-skywalking)
![Version](https://img.shields.io/pypi/pyversions/apache-skywalking)
![Build](https://github.com/apache/skywalking-python/actions/workflows/CI.yaml/badge.svg?event=push)

## Documentation

- [Official documentation](https://skywalking.apache.org/docs/#PythonAgent)
- [Blog](https://skywalking.apache.org/blog/2021-09-12-skywalking-python-profiling/) about the Python Agent Profiling Feature

## Capabilities

| Reporter  | Supported?      | Details                                                    | 
|:----------|:----------------|:-----------------------------------------------------------|
| Trace     | ✅ (default: ON) | Automatic instrumentation + Manual SDK                     |            
| Log       | ✅ (default: ON) | Direct reporter only. (Tracing context in log planned)     |
| Meter     | ✅ (default: ON) | Meter API + Automatic PVM metrics                          |
| Event     | ❌ (Planned)     | Report lifecycle events of your awesome Python application |
| Profiling | ✅ (default: ON) | Threading and Greenlet Profiler                            |

## Installation Requirements

SkyWalking Python Agent requires [Apache SkyWalking 8.0+](https://skywalking.apache.org/downloads/#SkyWalkingAPM) and Python 3.8+.

> If you would like to try out the latest features that are not released yet, please refer to this [guide](docs/en/setup/faq/How-to-build-from-sources.md) to build from sources.

## Live Demo
- Find the [live demo](https://skywalking.apache.org/#demo) with Python agent on our website.
- Follow the [showcase](https://skywalking.apache.org/docs/skywalking-showcase/next/readme/) to set up preview deployment quickly.

## Contributing

Before submitting a pull request or pushing a commit, please read our [contributing](CONTRIBUTING.md) and [developer guide](docs/en/contribution/Developer.md).

## Contact Us
* Mail list: **dev@skywalking.apache.org**. Mail to `dev-subscribe@skywalking.apache.org`, follow the reply to subscribe the mail list.
* Send `Request to join SkyWalking slack` mail to the mail list(`dev@skywalking.apache.org`), we will invite you in.
* Twitter, [ASFSkyWalking](https://twitter.com/AsfSkyWalking)
* For Chinese speaker, send `[CN] Request to join SkyWalking slack` mail to the mail list(`dev@skywalking.apache.org`), we will invite you in.
* [bilibili B站 视频](https://space.bilibili.com/390683219)

## License
Apache 2.0
