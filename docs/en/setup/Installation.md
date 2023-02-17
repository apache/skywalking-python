## Installation

**SkyWalking Python agent requires SkyWalking 8.0+ and Python 3.7+**

You can install the SkyWalking Python agent via various ways described next.

> **Already installed? Check out easy ways to start the agent in your application**

> [Non-intrusive <Recommended>](CLI.md) | [Intrusive <minimal>](Intrusive.md) | [Containerization](Container.md) 

> **All available configurations are listed [here](Configuration.md)**

## Important Note on Different Reporter Protocols

Currently only gRPC protocol fully supports [all available telemetry capabilities](../../README.md#capabilities) in the Python agent.

While gRPC is highly recommended, we provide alternative protocols to suit your production requirements.

Please refer to the table below before deciding which report protocol suits best for you.

| Reporter Protocol | Trace Reporter | Log Reporter | Meter Reporter | Profiling | 
|:------------------|:---------------|:-------------|:---------------|:----------|
| gRPC              | ✅              | ✅            | ✅              | ✅         |                
| HTTP              | ✅              | ✅            | ❌              | ❌         |                 
| Kafka             | ✅              | ✅            | ✅              | ❌         |     

### From PyPI

> If you want to try out the latest features that are not released yet, please refer to
> this [guide](faq/How-to-build-from-sources.md) to build from sources.

The Python agent module is published to [PyPI](https://pypi.org/project/apache-skywalking/), 
from where you can use `pip` to install:

```shell
# Install the latest version, using the default gRPC protocol to report data to OAP
pip install "apache-skywalking"

# Install support for every protocol (gRPC, HTTP, Kafka)
pip install "apache-skywalking[all]"

# Install the latest version, using the http protocol to report data to OAP
pip install "apache-skywalking[http]"

# Install the latest version, using the kafka protocol to report data to OAP
pip install "apache-skywalking[kafka]"

# Install a specific version x.y.z
# pip install apache-skywalking==x.y.z
pip install apache-skywalking==0.1.0  # For example, install version 0.1.0 no matter what the latest version is
```

### From Docker Hub

SkyWalking Python agent provides convenient dockerfile
and images for easy integration utilizing its [auto-bootstrap](CLI.md) capability.

Simply pull SkyWalking Python image from [Docker Hub](https://hub.docker.com/r/apache/skywalking-python)
based on desired agent version, protocol and Python version.

```dockerfile
FROM apache/skywalking-python:0.8.0-grpc-py3.10

# ... build your Python application

# If you prefer compact images (built from official Python slim image)

FROM apache/skywalking-python:0.8.0-grpc-py3.10-slim

# ... build your Python application
```

Then, You can build your Python application image based on our agent-enabled Python images and start
your applications with SkyWalking agent enabled for you. Please refer to our
[Containerization Guide](Container.md) for further instructions on integration and configuring.

### From Source Code

Please refer to the [How-to-build-from-sources FAQ](faq/How-to-build-from-sources.md).
