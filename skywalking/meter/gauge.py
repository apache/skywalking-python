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

from skywalking.meter.meter import BaseMeter, MeterType
from skywalking.protocol.language_agent.Meter_pb2 import MeterData, MeterSingleValue


class Gauge(BaseMeter):
    def __init__(self, name: str, generator, tags=None):
        super().__init__(name, tags)
        self.generator = generator

    def get(self):
        data = next(self.generator, None)
        return data if data else 0

    def transform(self):
        count = self.get()
        meterdata = MeterData(singleValue=MeterSingleValue(name=self.get_name(), labels=self.transform_tags(), value=count))
        return meterdata

    def get_type(self):
        return MeterType.GAUGE

    class Builder(BaseMeter.Builder):
        def __init__(self, name: str, generator, tags=None):
            self.meter = Gauge(name, generator, tags)
