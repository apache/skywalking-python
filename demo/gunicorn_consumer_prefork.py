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
This one demos how to use gunicorn with a simple fastapi uvicorn app.
"""
import logging

from fastapi import FastAPI

"""
# Run this to see sw-python working with gunicorn
sw-python -d run -p \
    gunicorn gunicorn_consumer_prefork:app \
    --workers 2 --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8088
"""

app = FastAPI()


@app.get('/cat')
async def application():
    try:
        logging.critical('fun cat got a request')
        return {'Cat Fun Fact': 'Fact is cat, cat is fat'}
    except Exception as e:  # noqa
        return {'message': str(e)}


if __name__ == '__main__':
    # noinspection PyTypeChecker
    # uvicorn.run(app, host='0.0.0.0', port=8088)
    ...
