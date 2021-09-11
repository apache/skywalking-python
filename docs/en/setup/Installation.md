## Installation

You can install the SkyWalking Python agent via various ways.

> If you want to try out the latest features that are not released yet, please refer to [the guide](docs/en/setup/FAQ.md#q-how-to-build-from-sources) to build from sources.

### From PyPI

The Python agent module is published to [PyPI](https://pypi.org/project/apache-skywalking/), from where you can use `pip` to install:

```shell
# Install the latest version, using the default gRPC protocol to report data to OAP
pip install "apache-skywalking"

# Install the latest version, using the http protocol to report data to OAP
pip install "apache-skywalking[http]"

# Install the latest version, using the kafka protocol to report data to OAP
pip install "apache-skywalking[kafka]"

# Install a specific version x.y.z
# pip install apache-skywalking==x.y.z
pip install apache-skywalking==0.1.0  # For example, install version 0.1.0 no matter what the latest version is
```

### From Docker Hub

SkyWalking Python agent provides convenient dockerfile and images for easy integration utilizing its 
[auto-bootstrap](CLI.md) capability.

You can build your Python application image based on our agent-enabled Python images and start
your applications with SkyWalking agent enabled for you. Please refer to our 
[Dockerfile Guide](Container.md) for further instructions on building and configuring.

### From Source Codes

Please refer to the [FAQ](FAQ.md#q-how-to-build-from-sources).