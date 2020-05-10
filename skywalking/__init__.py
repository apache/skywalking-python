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

import time
from collections import namedtuple
from enum import Enum
from typing import List


class Component(Enum):
    Unknown = 0
    General = 7000  # built-in modules that may not have a logo to display
    Flask = 7001


class Layer(Enum):
    Unknown = 0
    Database = 1
    RPCFramework = 2
    Http = 3
    MQ = 4
    Cache = 5


class Kind(Enum):
    Local = 0
    Entry = 1
    Exit = 2

    @property
    def is_local(self):
        return self == Kind.Local

    @property
    def is_entry(self):
        return self == Kind.Entry

    @property
    def is_exit(self):
        return self == Kind.Exit


LogItem = namedtuple('LogItem', 'key val')


class Log(object):

    def __init__(self, timestamp: time = time.time(), items: List[LogItem] = None):
        self.timestamp = timestamp
        self.items = items or []
