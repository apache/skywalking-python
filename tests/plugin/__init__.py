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
import sys
import unittest
from abc import ABC
from collections import namedtuple
from difflib import Differ
from os.path import dirname

import requests
import yaml
from requests import Response
from testcontainers.compose import DockerCompose

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

HostPort = namedtuple('HostPort', 'host port')
ServicePort = namedtuple('ServicePort', 'service port')


class BasePluginTest(unittest.TestCase, ABC):
    compose = None  # type: DockerCompose

    @classmethod
    def setUpClass(cls):
        cls.compose = DockerCompose(filepath=dirname(inspect.getfile(cls)))
        cls.compose.start()

        cls.compose.wait_for(cls.url(cls.collector_address()))

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

    def validate(self, expected_file_name=None):
        # type: (str) -> Response

        if expected_file_name is None:
            expected_file_name = os.path.join(dirname(inspect.getfile(self.__class__)), 'expected.data.yml')

        with open(expected_file_name) as expected_data_file:
            expected_data = os.linesep.join(expected_data_file.readlines())

            response = requests.post(
                url=self.__class__.url(self.__class__.collector_address(), path='/dataValidate'),
                data=expected_data,
            )

            if response.status_code != 200:
                res = requests.get(url=self.__class__.url(self.__class__.collector_address(), path='/receiveData'))

                actual_data = yaml.dump(yaml.load(res.content, Loader=Loader))

                differ = Differ()
                diff_list = list(differ.compare(
                    actual_data.splitlines(keepends=True),
                    yaml.dump(yaml.load(expected_data, Loader=Loader)).splitlines(keepends=True)
                ))

                print('diff list: ')

                sys.stdout.writelines(diff_list)

            self.assertEqual(response.status_code, 200)

            return response
