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

import os
import time
import unittest
from os.path import abspath, dirname

import requests
from testcontainers.compose import DockerCompose

from tests.plugin import BasePluginTest


class TestRequestPlugin(BasePluginTest):
    @classmethod
    def setUpClass(cls):
        cls.compose = DockerCompose(filepath=dirname(abspath(__file__)))
        cls.compose.start()

        cls.compose.wait_for(cls.url(cls.collector_address()))

    def test_request_plugin(self):
        print('traffic: ', requests.post(url=self.url(('consumer', '9090'))))

        time.sleep(3)

        self.validate(expected_file_name=os.path.join(dirname(abspath(__file__)), 'expected.data.yml'))


if __name__ == '__main__':
    unittest.main()
