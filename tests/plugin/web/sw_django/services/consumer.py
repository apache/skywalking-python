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

import sys

import requests
from django.conf import settings
from django.conf.urls import url
from django.http import JsonResponse

settings.configure(
    DEBUG=True,
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=['*'],
)


def index(request):
    res = requests.post('http://provider:9091/users', timeout=5)
    return JsonResponse(res.json())


urlpatterns = (
    url('users', index),
)


if __name__ == '__main__':
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
