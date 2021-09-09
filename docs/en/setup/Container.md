# Apache SkyWalking Python Agent dockerfile and images

**Docker images are not official ASF releases but provided for convenience. Recommended usage is always to build the
source**

**<img src="http://skywalking.apache.org/assets/logo.svg" alt="SkyWalking logo" height="90px" align="right" />**

**SkyWalking**: an APM(application performance monitor) system, especially designed for microservices, cloud native and
container-based (Docker, Kubernetes, Mesos) architectures.

[![GitHub stars](https://img.shields.io/github/stars/apache/skywalking.svg?style=for-the-badge&label=Stars&logo=github)](https://github.com/apache/skywalking)
[![Twitter Follow](https://img.shields.io/twitter/follow/asfskywalking.svg?style=for-the-badge&label=Follow&logo=twitter)](https://twitter.com/AsfSkyWalking)

This image hosts the SkyWalking Python agent package on top of official Python base images providing support from 
Python 3.5 - 3.9.

## How to use this image

The images are hosted at [Docker Hub](https://hub.docker.com/r/apache/skywalking-python) and available from the `skywalking.docker.scarf.sh` endpoint.

`skywalking.docker.scarf.sh/apache/skywalking-python`

### Build your Python application image on top of this image

Start by pulling the skywalking-python image as the base of your application image.
Refer to [Docker Hub](https://hub.docker.com/r/apache/skywalking-python) for the list of tags available.

```dockerfile
FROM apache/skywalking-python:0.7.0-grpc-py3.9

# ... build your Python application
```

You could start your Python application with `CMD`. For example - `CMD ['gunicorn', 'app.wsgi']` 

You don't need to care about enabling the SkyWalking Python agent manually, 
it should be adopted and bootstrapped automatically through the `sw-python` CLI.

[Environment variables](EnvVars.md) can be provided to customize the agent behavior.

### Build an image from the dockerfile 

Provide the following arguments to build your own image from the dockerfile.

```text
BASE_IMAGE # the Python base image to build upon
SW_PYTHON_AGENT_VERSION # agent version to be pulled from PyPI
SW_PYTHON_AGENT_PROTOCOL # agent protocol - grpc/ http/ kafka
```

## License

[Apache 2.0 License.](/LICENSE)
