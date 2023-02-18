#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import inspect
import os
import time
from os.path import dirname
from typing import Callable

import pytest
from _pytest.fixtures import FixtureRequest
from testcontainers.compose import DockerCompose


@pytest.fixture
def version():
    # type: () -> str
    return ''


# noinspection PyUnusedLocal
@pytest.fixture
def prepare():
    # type: () -> Callable
    return lambda *_: None


@pytest.fixture
def docker_compose(request: FixtureRequest, prepare: Callable, version: str) -> None:
    module = request.module
    cwd = dirname(inspect.getfile(module))

    if version:
        with open(os.path.join(cwd, 'requirements.txt'), mode='w') as req:
            req.write(version)

    with DockerCompose(filepath=cwd) as compose:
        exception = None
        exception_delay = 0
        stdout, stderr = None, None
        for _ in range(50):
            try:
                time.sleep(3)
                prepare()
                exception = None
                break
            except Exception as e:
                exception_delay += 3
                exception = e
                stdout, stderr = compose.get_logs()
        else:  # when exception isn't in prepare,  e.g. system-level/pip error/healthcheck stuck
            exception = exception or 'Exception is in container startup, please pay attention to log and ' \
                                     'ensure system/python package installation or healthcheck utility is working'
            stdout, stderr = compose.get_logs()

        if exception:
            print(f'STDOUT:\n{stdout.decode("utf-8")}')
            print('==================================')
            print(f'STDERR:\n{stderr.decode("utf-8")}')

            raise Exception(f"""Wait time exceeded {exception_delay} secs. {exception}""")

        yield compose
