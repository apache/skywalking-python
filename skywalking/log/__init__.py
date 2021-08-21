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

import logging
import traceback

from skywalking.log import sw_logging
from skywalking.loggings import logger


def install():
    logger.debug('Installing plugin for logging module')
    # noinspection PyBroadException
    try:
        sw_logging.install()
    except Exception:
        logger.warning('Failed to install sw_logging plugin')
        traceback.print_exc() if logger.isEnabledFor(logging.DEBUG) else None
