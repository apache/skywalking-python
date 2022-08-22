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
from skywalking.protocol.language_agent.Meter_pb2 import Label

from enum import Enum
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
    
    def getKey(self):
        return self.key
    
    def getValue(self):
        return self.value

    def __hash__(self) -> int:
        return hash((self.key, self.value))

class MeterId():
    def __init__(self, name: str, type, tags: list) -> None:
        self.name = name
        self.type = type
        self.tags = tags
        self.labels = None
    
    def transformTags(self):
        if self.labels != None:
            return self.labels

        self.labels = list(map(lambda tag: Label(name=tag.key, value=tag.value), self.tags))
        return self.labels
    
    def getName(self):
        return self.name
    
    def getTags(self):
        return self.tags
    
    def getType(self):
        return self.type
    
    def __hash__(self):
        return hash((self.name, self.type, tuple(self.tags)))


class BaseMeter():
    meter_service = None
    def __init__(self, name: str, tags=[]):
        self.meterId = MeterId(name, self.getType(), tags)
        if not BaseMeter.meter_service:
            from skywalking.agent import meter_service_thread
            BaseMeter.meter_service = meter_service_thread

    def getName(self):
        return self.meterId.getName()

    def getTag(self, tagKey):
        for tag in self.meterId.getTags():
            if tag.getKey() == tagKey:
                return tag.getValue()

    def getId(self):
        return self.meterId

    def transformTags(self):
        return self.getId().transformTags()
    
    def tag(self, name: str, value):
        self.meterId.getTags().append(MeterTag(name, value))
        return self

    def build(self):
        self.meterId.getTags().sort()
        BaseMeter.meter_service.register(self)
    
    @abstractmethod
    def getType(self):
        pass

    
    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self):
        pass
