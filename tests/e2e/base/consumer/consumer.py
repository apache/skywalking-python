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
This module contains the Consumer part of the e2e tests.
consumer (FastAPI) -> consumer (AIOHTTP) -> provider (FastAPI + logging_with_exception)
"""
import aiohttp
import uvicorn
from fastapi import FastAPI
from fastapi import Request

app = FastAPI()


@app.get('/artist')
@app.post('/artist')
async def application(request: Request):
    try:
        payload = await request.json()
        async with aiohttp.ClientSession() as session:
            async with session.post('http://provider:9090/artist', data=payload) as response:
                return await response.json()
    except Exception:  # noqa
        return {'message': 'Error'}


if __name__ == '__main__':
    # noinspection PyTypeChecker
    uvicorn.run(app, host='0.0.0.0', port=9090)
