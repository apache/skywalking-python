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
import unittest
from abc import ABC
from collections import namedtuple

import requests
from requests import Response
from testcontainers.compose import DockerCompose

HostPort = namedtuple('HostPort', 'host port')
ServicePort = namedtuple('ServicePort', 'service port')


class BasePluginTest(unittest.TestCase, ABC):
    compose = None  # type: DockerCompose

    @classmethod
    def tearDownClass(cls):
        cls.compose.stop()

    @classmethod
    def host(cls, service_port):
        # type: (ServicePort) -> str
        service, port = service_port
        return cls.compose.get_service_host(service_name=service, port=port)

    @classmethod
    def port(cls, service_port):
        # type: (ServicePort) -> str
        service, port = service_port
        return cls.compose.get_service_port(service_name=service, port=port)

    @classmethod
    def url(cls, service_port, path=''):
        # type: (ServicePort, str) -> str
        return 'http://%s:%s/%s' % (cls.host(service_port), cls.port(service_port), path.lstrip('/'))

    @classmethod
    def collector_address(cls):
        # type: () -> ServicePort
        return ServicePort(service='collector', port='12800')

    def validate(self, expected_file_name):
        # type: (str) -> Response
        with open(expected_file_name) as expected_data_file:
            response = requests.post(
                url=self.__class__.url(self.__class__.collector_address(), path='/dataValidate'),
                data=os.linesep.join(expected_data_file.readlines()),
            )
            print('validate: ', response)

        self.assertEqual(response.status_code, 200)

        return response
