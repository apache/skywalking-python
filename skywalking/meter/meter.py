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
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from skywalking.protocol.language_agent.Meter_pb2 import Label
import skywalking.meter as meter


class MeterType(Enum):
    GAUGE = 1
    COUNTER = 2
    HISTOGRAM = 3


class MeterTag():
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    def __lt__(self, other):
        if self.key != other.key:
            return self.key < other.key
        else:
            return self.value < other.value

    def get_key(self):
        return self.key

    def get_value(self):
        return self.value

    def __hash__(self) -> int:
        return hash((self.key, self.value))


class MeterId():
    def __init__(self, name: str, type, tags: tuple) -> None:
        if tags is None:
            tags = ()

        self.name = name
        self.type = type
        self.tags = [MeterTag(key, value) for (key, value) in tags]
        self.labels = None

    def transform_tags(self):
        if self.labels is not None:
            return self.labels

        self.labels = [Label(name=tag.key, value=tag.value) for tag in self.tags]
        return self.labels

    def get_name(self):
        return self.name

    def get_tags(self):
        return self.tags

    def get_type(self):
        return self.type

    def __hash__(self):
        return hash((self.name, self.type, tuple(self.tags)))


class BaseMeter(ABC):
    meter_service = None

    def __init__(self, name: str, tags=None):
        # Should always override to use the correct meter service.
        # Otherwise, forked process will inherit the original
        # meter_service in parent. We want a new one in child.
        BaseMeter.meter_service = meter._meter_service
        self.meterId = MeterId(name, self.get_type(), tags)

    def get_name(self):
        return self.meterId.get_name()

    def get_tag(self, tag_key):
        for tag in self.meterId.get_tags():
            if tag.get_key() == tag_key:
                return tag.get_value()

    def get_id(self):
        return self.meterId

    def transform_tags(self):
        return self.get_id().transform_tags()

    @abstractmethod
    def get_type(self):
        pass

    class Builder(ABC):
        @abstractmethod
        def __init__(self, name: str, tags=None):
            # Derived Builder should instantiate its corresponding meter here.
            # self.meter = BaseMeter(name, tags)
            self.meter: Optional[BaseMeter] = None
            pass

        def tag(self, name: str, value):
            self.meter.meterId.get_tags().append(MeterTag(name, value))
            return self

        def build(self):
            self.meter.meterId.get_tags().sort()
            BaseMeter.meter_service.register(self.meter)
            return self.meter
