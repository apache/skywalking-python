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
Here is the practice I employed.

Create a file in the folder you just cloned.
```
FROM python:3.8

WORKDIR /usr/src/app

COPY . .

RUN pip install -r requirements.txt
RUN pip install -e .[test]
then
```

Then run the command below to create the docker image we need later. Because the test process runs in the docker container, we need to apply the changes you did to the docker image. You may need to run this command whenever you change any files before the test.
```
docker build -t apache/skywalking-python-agent:latest-plugin .  -f Dockerfile.test 
```

Then ``make test`` will run as expected.
