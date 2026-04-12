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

from skywalking.plugins.sw_urllib3 import support_matrix as v1_matrix
from skywalking.plugins.sw_urllib3_v2 import support_matrix as v2_matrix
from tests.orchestrator import get_test_vector
from tests.plugin.base import TestPluginBase

# Merge v1 and v2 test vectors — get_test_vector returns versions for the current Python
_versions = (get_test_vector(lib_name='urllib3', support_matrix=v1_matrix)
             + get_test_vector(lib_name='urllib3', support_matrix=v2_matrix))


@pytest.fixture
def prepare():
    # type: () -> Callable
    return lambda *_: requests.get('http://0.0.0.0:9090/users', timeout=5)


class TestPlugin(TestPluginBase):
    @pytest.mark.parametrize('version', _versions)
    def test_plugin(self, docker_compose, version):
        self.validate()
