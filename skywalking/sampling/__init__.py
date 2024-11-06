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
from typing import Optional


sampling_service = None


def init(force: bool = False):
    """
    If the sampling service is not initialized, initialize it.
    if force, we are in a fork(), we force re-initialization
    """
    from skywalking.sampling.sampling_service import SamplingService
    from skywalking.log import logger

    global sampling_service
    if sampling_service and not force:
        return

    logger.debug('Initializing sampling service')
    sampling_service = SamplingService()
    sampling_service.start()


async def init_async(async_event: Optional[asyncio.Event] = None):
    from skywalking.sampling.sampling_service import SamplingServiceAsync

    global sampling_service

    sampling_service = SamplingServiceAsync()
    if async_event is not None:
        async_event.set()
    task = asyncio.create_task(sampling_service.start())
    sampling_service.strong_ref_set.add(task)
