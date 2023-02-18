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
import time
import random
import os
from flask import Flask

from log_formatter import E2EProviderFormatter

app = Flask(__name__)
formatter = E2EProviderFormatter(logging.BASIC_FORMAT)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

e2e_provider_logger = logging.getLogger('__name__')
e2e_provider_logger.setLevel(logging.INFO)
e2e_provider_logger.addHandler(stream_handler)


@app.route('/pid', methods=['GET'])
def pid():
    """
    This endpoint is used to get the pid of the provider, for e2e tests.
    Returns: The instance name of the provider.
    """
    from skywalking import config
    # Instance name is dynamically modified by uwsgi hook/os.fork handler

    return {'instance': config.agent_instance_name}


@app.route('/artist-provider', methods=['POST'])
def artist():
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

    return {
        'artist': 'Luis Fonsi',
        'pid': os.getpid()
    }


if __name__ == '__main__':
    # noinspection PyTypeChecker
    app.run(host='0.0.0.0', port=9090)
