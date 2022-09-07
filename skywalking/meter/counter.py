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

import timeit
from enum import Enum
from skywalking.meter.meter import BaseMeter, MeterType
from skywalking.protocol.language_agent.Meter_pb2 import MeterData, MeterSingleValue


class CounterMode(Enum):
    INCREMENT = 1
    RATE = 2


class Counter(BaseMeter):
    def __init__(self, name: str, mode: CounterMode, tags=None):
        super().__init__(name, tags)
        self.count = 0
        self.previous = 0
        self.mode = mode

    def increment(self, value):
        self.count += value

    def get(self):
        return self.count

    def transform(self):
        current_value = self.get()
        if self.mode == CounterMode.RATE:
            self.previous = current_value
            count = current_value - self.previous
        else:
            count = current_value

        meterdata = MeterData(singleValue=MeterSingleValue(name=self.get_name(), labels=self.transform_tags(), value=count))
        return meterdata

    def mode(self, mode):
        self.mode = mode
        return self

    def get_type(self):
        return MeterType.COUNTER

    def create_timer(self):
        return Counter.Timer(self)

    class Timer():
        def __init__(self, metrics):
            self.metrics = metrics

        def __enter__(self):
            self.start = timeit.default_timer()

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.stop = timeit.default_timer()
            duration = self.stop - self.start
            self.metrics.increment(duration)

    @staticmethod
    def timer(name: str):
        def inner(func):
            def wrapper(*args, **kwargs):
                start = timeit.default_timer()
                func(*args, **kwargs)
                stop = timeit.default_timer()
                duration = stop - start
                counter = Counter.meter_service.get_meter(name)
                counter.increment(duration)

            return wrapper

        return inner

    @staticmethod
    def increase(name: str, num=1):
        def inner(func):
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
                counter = Counter.meter_service.get_meter(name)
                counter.increment(num)

            return wrapper

        return inner
