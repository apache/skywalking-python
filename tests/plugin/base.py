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
import time
from abc import ABC
from difflib import Differ
from os.path import dirname

import requests
import yaml
from requests import Response

try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader


class TestPluginBase(ABC):
    def validate(self, expected_file_name=None):
        # type: (str) -> Response

        if expected_file_name is None:
            expected_file_name = os.path.join(dirname(inspect.getfile(self.__class__)), 'expected.data.yml')

        time.sleep(10)

        with open(expected_file_name) as expected_data_file:
            expected_data = os.linesep.join(expected_data_file.readlines())

            response = requests.post(url='http://0.0.0.0:12800/dataValidate', data=expected_data)

            if response.status_code != 200:
                res = requests.get('http://0.0.0.0:12800/receiveData')

                actual_data = yaml.dump(yaml.load(res.content, Loader=Loader))

                differ = Differ()
                diff_list = list(differ.compare(
                    actual_data.splitlines(keepends=True),
                    yaml.dump(yaml.load(expected_data, Loader=Loader)).splitlines(keepends=True)
                ))

                print('diff list: ')

                sys.stdout.writelines(diff_list)

            assert response.status_code == 200

            return response
