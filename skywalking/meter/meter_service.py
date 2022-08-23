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

from time import time
from threading import Thread
from skywalking import config
from skywalking.meter.meter import BaseMeter


class MeterService(Thread):
    __finished = None
    logger = None

    def __init__(self, reporter, ___finished, _logger):
        super().__init__()
        if not MeterService.__finished:
            MeterService.__finished = ___finished
            MeterService.logger = _logger

        self.meterMap = {}
        self.reporter = reporter

    def register(self, meter: BaseMeter):
        self.meterMap[meter.get_id().get_name()] = meter

    def get_meter(self, name: str):
        return self.meterMap.get(name)

    def send(self):

        def transform(adapter):
            meterdata = adapter.transform()
            meterdata.service = config.service_name
            meterdata.serviceInstance = config.service_instance
            meterdata.timestamp = int(time()*1000)
            return meterdata

        wait = base = 1

        while not MeterService.__finished.is_set():
            try:
                meterdata_ls = [transform(meterdata) for meterdata in self.meterMap.values()]
                generator = iter(meterdata_ls)
                self.reporter.report(generator)
                wait = base
            except Exception as exc:
                MeterService.logger.error(str(exc))
                wait = min(60, wait * 2 or 1)

            MeterService.__finished.wait(wait)


    def run(self):
        while True:
            self.send()
