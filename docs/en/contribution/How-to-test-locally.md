# How to test locally?

This guide assumes you just cloned the repo and are ready to make some changes.

After cloning the repo, make sure you also have cloned the submodule for protocol. Otherwise, run the command below. 
```
git submodule update --init
```

Then run ``make setup-test``. This will create virtual environments for python and generate the protocol folder needed for the agent.

By now, you can do what you want.

Let's get to the topic of how to test.
The test process requires docker and docker-compose throughout. If you haven't installed them, please install them first.

In the test process, the script will create several docker containers based on a particular docker image(apache/skywalking-python-agent:latest-plugin), but the current script does not create this docker image automatically. So we need to create manually.
```
docker build --build-arg BASE_PYTHON_IMAGE=3.6 -t apache/skywalking-python-agent:latest-plugin --no-cache . -f tests/plugin/Dockerfile.plugin
```
By the way, because the test process runs in the docker container, we need to apply the changes you did to the docker image. You may need to run this command whenever you change files before the test.

Then ``make test`` will run as expected.

