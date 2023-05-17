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

from asyncio import Event

from skywalking.meter.gauge import Gauge


class DataSource:
    def register(self):
        for name in dir(self):
            if name.endswith('generator'):
                generator = getattr(self, name)()
                Gauge.Builder('instance_pvm_' + name[:-10], generator).build()

    async def register_async(self, async_event: Event):
        await async_event.wait()
        for name in dir(self):
            if name.endswith('generator'):
                generator = getattr(self, name)()
                Gauge.Builder('instance_pvm_' + name[:-10], generator).build()
