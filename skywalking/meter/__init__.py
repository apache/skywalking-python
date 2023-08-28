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

import asyncio

_meter_service = None


def init(force: bool = False):
    """
    If the meter service is not initialized, initialize it.
    if force, we are in a fork(), we force re-initialization
    """
    from skywalking.meter.meter_service import MeterService

    global _meter_service
    if _meter_service and not force:
        return

    _meter_service = MeterService()
    _meter_service.start()


async def init_async(async_event: asyncio.Event = None):
    from skywalking.meter.meter_service import MeterServiceAsync

    global _meter_service

    _meter_service = MeterServiceAsync()
    if async_event is not None:
        async_event.set()
    task = asyncio.create_task(_meter_service.start())
    _meter_service.strong_ref_set.add(task)
