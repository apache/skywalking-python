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

import re
import traceback
from urllib.parse import urlparse

from skywalking import config


def sw_urlparse(url):
    # Removes basic auth credentials from netloc
    url_param = urlparse(url)
    safe_netloc = url_param.netloc
    try:
        safe_netloc = f"{url_param.hostname}{f':{str(url_param.port)}' if url_param.port else ''}"
    except ValueError:  # illegal url, skip
        pass

    return url_param._replace(netloc=safe_netloc)


def sw_filter(target: str):
    # Remove user:pw from any valid full urls

    return re.sub(r'://(.*?)@', r'://', target)


def sw_traceback():
    stack_trace = traceback.format_exc(limit=config.cause_exception_depth)

    return sw_filter(target=stack_trace)
