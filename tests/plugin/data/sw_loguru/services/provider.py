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
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import logging
import time

from loguru import logger

if __name__ == '__main__':
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI()

    logging_logger = logging.getLogger()


    @app.get('/users')
    async def application():
        time.sleep(0.5)

        try:
            raise Exception('Loguru Exception Test.')
        except Exception:  # noqa
            logger.opt(exception=True).error('Loguru provider error reported.')
            logging_logger.error('Logging provider error reported.', exc_info=True)

        # this will be filtered by SW_AGENT_LOG_REPORTER_LEVEL
        logger.debug('Loguru provider debug reported.')

        logger.warning('Loguru provider warning reported.')

        logging_logger.critical('Logging provider critical reported.')

        return {'song': 'Despacito', 'artist': 'Luis Fonsi'}


    # error level filter the uvicorn's log by logging
    uvicorn.run(app, host='0.0.0.0', port=9091, log_level='error')
