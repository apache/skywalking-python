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
from typing import Callable

import pytest
import requests

from tests.plugin.base import TestPluginBase


@pytest.fixture
def prepare():
    # type: () -> Callable
    return lambda *_: requests.get('http://0.0.0.0:9090/users', timeout=5).raise_for_status()


class TestPlugin(TestPluginBase):
    """
    Explicit os.fork() with SW_AGENT_EXPERIMENTAL_FORK_SUPPORT: the parent keeps its
    agent, the forked child restarts one as a `-child(pid)` instance, and the trace
    stays continuous across the fork (parent entry/exit -> child entry with ref).
    Runs over the HTTP reporter: forking with a live gRPC channel is subject to
    upstream at-fork races (grpc/grpc#43055) that can silently drop either side's
    segments; the gRPC transport path is covered deterministically by sw_gunicorn.
    """

    @pytest.mark.parametrize('version', ['grpcio>=1.83'])
    def test_plugin(self, docker_compose, version):
        self.validate()

        stdout, stderr = docker_compose.get_logs()
        stdout = stdout.decode('utf-8') if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode('utf-8') if isinstance(stderr, bytes) else stderr
        logs = f'{stdout}\n{stderr}'

        # parent started one full agent, the forked child restarted one
        assert logs.count('starting in pid-') == 1
        assert logs.count('Agent spawned as') == 1
