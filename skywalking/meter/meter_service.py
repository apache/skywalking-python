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
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from skywalking import config
from skywalking import agent
from skywalking.meter.meter import BaseMeter
from skywalking.utils.time import current_milli_time
from skywalking.config import meter_reporter_peroid


class MeterService(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.meter_map = {}

    def register(self, meter: BaseMeter):
        self.meter_map[meter.get_id().get_name()] = meter

    def get_meter(self, name: str):
        return self.meter_map.get(name)

    def send(self):

        def archive(meterdata):
            meterdata = meterdata.transform()
            meterdata.service = config.service_name
            meterdata.serviceInstance = config.service_instance
            meterdata.timestamp = current_milli_time()
            agent.archive_meter(meterdata)

        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.map(archive, self.meter_map.values())

    def run(self):
        while True:
            time.sleep(meter_reporter_peroid)
            self.send()
