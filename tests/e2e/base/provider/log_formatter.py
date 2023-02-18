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
import io
import logging
import traceback


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
