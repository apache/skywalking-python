# Apache SkyWalking Python Image Release Guide

The official process generating a list of images covering most used Python versions and variations(grpc/http/kafka) of the Python agent is deployed to our GitHub actions and therefore do not rely on this documentation.

This documentation shows the way to build and push the SkyWalking Python images manually. 

## How to build manually

Before building the latest release of images, make sure an official release is pushed to PyPI where the dockerfile will depend on.

## Images

The process generating a list of images covering most used Python versions and variations(grpc/http/kafka) of the Python agent is deployed to
our GitHub actions.

The convenience images are published to [DockerHub](https://hub.docker.com/r/apache/skywalking-python)

## How to build

Issue the following commands to build relevant docker images for the Python agent.
The `make` command will generate three images(grpc, http, kafka) for each Python version supported.

At the root folder -
```shell
export AGENT_VERSION=<version>

make build-image
```

Or at the docker folder -
```shell
cd docker

export AGENT_VERSION=<version>

make
```

## How to publish images
After a SkyWalking Apache release for the Python agent and wheels have been pushed to PyPI:


1. Build images from the project root, this step pulls agent wheel from PyPI and installs it:
    
    ```shell
    export AGENT_VERSION=<version>

    make build-image
    ```


2. Verify the images built.


3. Push built images to docker hub repos:

   ```shell
   make push-image
   ```
