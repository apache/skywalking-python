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
from websockets.client import connect

import asyncio

if __name__ == '__main__':
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI()

    @app.get('/ws')
    async def websocket_ping():
        async with connect('ws://provider:9091/ws', extra_headers=None) as websocket:
            await websocket.send('Ping')

            response = await websocket.recv()
            await asyncio.sleep(0.5)

            await websocket.close()
            return response

    uvicorn.run(app, host='0.0.0.0', port=9090)
