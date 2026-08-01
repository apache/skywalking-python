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
    Regression test for Gunicorn prefork over the gRPC reporter, apache/skywalking#13958.
    Validates a complete cross-process trace (consumer entry/exit -> gunicorn provider entry)
    plus: the master runs no gRPC channel before fork, every worker boots and reports, and
    grpcio >= 1.80 produces no poll-engine fork errors.
    """

    @pytest.mark.parametrize('version', ['grpcio>=1.83'])
    def test_plugin(self, docker_compose, version):
        self.validate()

        stdout, stderr = docker_compose.get_logs()
        stdout = stdout.decode('utf-8') if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode('utf-8') if isinstance(stderr, bytes) else stderr
        logs = f'{stdout}\n{stderr}'

        # every worker booted exactly once (2 provider + 1 provider-async); a worker
        # deadlocked at fork would be killed by the arbiter and respawned -> extra boot lines
        assert logs.count('Booting worker with pid') == 3
        assert 'WORKER TIMEOUT' not in logs

        # full agent started in each provider worker, instrumentation-only in the master;
        # the single full start belongs to the consumer
        assert logs.count('Agent spawned as') == 2
        assert 'instrumented pre-fork master' in logs
        assert logs.count('starting in pid-') == 1

        # asyncio enhancement + prefork must be rejected, not started unsafely
        assert 'does not support pre-forking' in logs

        # grpcio >= 1.80 EventEngine fork regression signature
        assert 'Kick Failure' not in logs
        assert 'pollset_kick' not in logs
