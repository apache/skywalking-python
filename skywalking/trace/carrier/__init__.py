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

from typing import List

from skywalking.utils.lang import b64encode, b64decode


class CarrierItem(object):
    def __init__(self, key: str = '', val: str = ''):
        self.key = key  # type: str
        self.val = val  # type: str

    @property
    def key(self):
        return self.__key

    @key.setter
    def key(self, key: str):
        self.__key = key

    @property
    def val(self):
        return self.__val

    @val.setter
    def val(self, val: str):
        self.__val = val


class Carrier(CarrierItem):
    def __init__(self):
        super(Carrier, self).__init__(key='sw8')
        self.trace_id = ''  # type: str
        self.segment_id = ''  # type: str
        self.span_id = ''  # type: str
        self.service = ''  # type: str
        self.service_instance = ''  # type: str
        self.endpoint = ''  # type: str
        self.client_address = ''  # type: str
        self.items = [self]  # type: List[CarrierItem]
        self.__iter_index = 0  # type: int

    @property
    def val(self) -> str:
        return '-'.join([
            '1',
            b64encode(self.trace_id),
            b64encode(self.segment_id),
            self.span_id,
            b64encode(self.service),
            b64encode(self.service_instance),
            b64encode(self.endpoint),
            b64encode(self.client_address),
        ])

    @val.setter
    def val(self, val: str):
        self.__val = val
        if not val:
            return
        parts = val.split('-')
        if len(parts) != 8:
            return
        self.trace_id = b64decode(parts[1])
        self.segment_id = b64decode(parts[2])
        self.span_id = parts[3]
        self.service = b64decode(parts[4])
        self.service_instance = b64decode(parts[5])
        self.endpoint = b64decode(parts[6])
        self.client_address = b64decode(parts[7])

    @property
    def is_valid(self):
        # type: () -> bool
        return len(self.trace_id) > 0 and \
               len(self.segment_id) > 0 and \
               len(self.service) > 0 and \
               len(self.service_instance) > 0 and \
               len(self.endpoint) > 0 and \
               len(self.client_address) > 0 and \
               self.span_id.isnumeric()

    def __iter__(self):
        self.__iter_index = 0
        return self

    def __next__(self):
        if self.__iter_index >= len(self.items):
            raise StopIteration
        n = self.items[self.__iter_index]
        self.__iter_index += 1
        return n
