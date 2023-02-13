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

import uvicorn
from fastapi import FastAPI
import httpx

async_client = httpx.AsyncClient()
client = httpx.Client()
app = FastAPI()


@app.post('/users')
async def application():
    try:
        await async_client.post('http://provider:9091/users')
        res = client.post('http://provider:9091/users')

        return res.json()
    except Exception:  # noqa
        return {'message': 'Error'}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=9090)
