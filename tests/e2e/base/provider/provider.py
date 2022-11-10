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

"""
This module contains the Provider part of the e2e tests.
consumer (FastAPI) -> consumer (AIOHTTP) -> provider (FastAPI + logging_with_exception)
We also cover the usage of logging interception in this module.
"""
import io
import logging
import random
import time
import traceback

import uvicorn
from fastapi import FastAPI


class E2EProviderFormatter(logging.Formatter):
    """
    User defined formatter should in no way be
    interfered by the log reporter formatter.
    """

    def format(self, record):
        result = super().format(record)
        return f'e2e_provider:={result}'

    def formatException(self, ei):  # noqa
        """
        Mock user defined formatter which limits the traceback depth
        to None -> meaning it will not involve trackback at all.
        but the agent should still be able to capture the traceback
        at default level of 5 by ignoring the cache.
        """
        sio = io.StringIO()
        tb = ei[2]
        traceback.print_exception(ei[0], ei[1], tb, None, sio)
        s = sio.getvalue()
        sio.close()
        if s[-1:] == '\n':
            s = s[:-1]
        return s


formatter = E2EProviderFormatter(logging.BASIC_FORMAT)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

e2e_provider_logger = logging.getLogger('__name__')
e2e_provider_logger.setLevel(logging.INFO)
e2e_provider_logger.addHandler(stream_handler)

app = FastAPI()


@app.get('/artist')
@app.post('/artist')
async def application():
    time.sleep(random.random())
    # Exception is reported with trackback depth of 5 (default)
    try:
        raise Exception('E2E Provider Exception Text!')
    except Exception:  # noqa
        e2e_provider_logger.exception('E2E Provider Exception, this is reported!')
    # FIXME - a temp workaround of a flaky test related to issue #8752
    # Later arrived logs are at top of list, thus q
    time.sleep(0.5)
    # Warning is reported
    e2e_provider_logger.warning('E2E Provider Warning, this is reported!')
    time.sleep(0.5)
    # The user:password part will be removed
    e2e_provider_logger.warning('Leak basic auth info at https://user:password@example.com')
    # Debug is not reported according to default agent setting
    e2e_provider_logger.debug('E2E Provider Debug, this is not reported!')

    return {'artist': 'Luis Fonsi'}


if __name__ == '__main__':
    # noinspection PyTypeChecker
    uvicorn.run(app, host='0.0.0.0', port=9090)
