# Apache SkyWalking Python Agent dockerfile and images

**Docker images are not official ASF releases but provided for convenience. Recommended usage is always to build the
source**

This image hosts the SkyWalking Python agent package on top of official Python base images (full & slim) providing support from 
Python 3.8 - 3.11.

## How to use this image

The images are hosted at [Docker Hub](https://hub.docker.com/r/apache/skywalking-python).

The images come with protocol variants(gRPC, Kafka, HTTP) and base Python variants(Full, Slim).

### Build your Python application image on top of this image

Start by pulling the `skywalking-python` image as the base of your application image.
Refer to [Docker Hub](https://hub.docker.com/r/apache/skywalking-python) for the list of tags available.

```dockerfile
FROM apache/skywalking-python:1.1.0-grpc-py3.10

# ... build your Python application
```

You could start your Python application with `CMD`. The Python image already sets an entry point `ENTRYPOINT ["sw-python"]`.

For example - `CMD ['run', '-p', 'gunicorn', 'app.wsgi']` 
**`-p` is always needed when using with Gunicorn/uWSGI** -> This will be translated to `sw-python run -p gunicorn app.wsgi`

You don't need to care about enabling the SkyWalking Python agent manually, 
it should be adopted and bootstrapped automatically through the `sw-python` CLI.

[Environment variables](Configuration.md) should be provided to customize the agent behavior.

### Build an image from the dockerfile 

Provide the following arguments to build your own image from the dockerfile.

```text
BASE_PYTHON_IMAGE # the Python base image to build upon
SW_PYTHON_AGENT_VERSION # agent version to be pulled from PyPI
SW_PYTHON_AGENT_PROTOCOL # agent protocol - grpc/ http/ kafka
```
