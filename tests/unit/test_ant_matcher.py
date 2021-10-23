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

import unittest

from skywalking import config


def fast_path_match(pattern, path):
    config.trace_ignore_path = pattern
    config.finalize()

    return config.RE_IGNORE_PATH.match(path)


class TestFastPathMatch(unittest.TestCase):
    def test_match(self):
        pattern = '/eureka/*'
        path = '/eureka/apps'
        assert fast_path_match(pattern, path) is True
        path = '/eureka/'
        assert fast_path_match(pattern, path) is True
        path = '/eureka/apps/'
        assert fast_path_match(pattern, path) is False

        pattern = '/eureka/*/'
        path = '/eureka/apps/'
        assert fast_path_match(pattern, path) is True
        path = '/eureka/'
        assert fast_path_match(pattern, path) is False
        path = '/eureka/apps/list'
        assert fast_path_match(pattern, path) is False

        pattern = '/eureka/**'
        path = '/eureka/'
        assert fast_path_match(pattern, path) is True
        path = '/eureka/apps/test'
        assert fast_path_match(pattern, path) is True
        path = '/eureka/apps/test/'
        assert fast_path_match(pattern, path) is False

        pattern = 'eureka/apps/?'
        path = 'eureka/apps/list'
        assert fast_path_match(pattern, path) is False
        path = 'eureka/apps/'
        assert fast_path_match(pattern, path) is False
        path = 'eureka/apps/a'
        assert fast_path_match(pattern, path) is True

        pattern = 'eureka/**/lists'
        path = 'eureka/apps/lists'
        assert fast_path_match(pattern, path) is True
        path = 'eureka/apps/test/lists'
        assert fast_path_match(pattern, path) is True
        path = 'eureka/apps/test/'
        assert fast_path_match(pattern, path) is False
        path = 'eureka/apps/test'
        assert fast_path_match(pattern, path) is False

        pattern = 'eureka/**/test/**'
        path = 'eureka/apps/test/list'
        assert fast_path_match(pattern, path) is True
        path = 'eureka/apps/foo/test/list/bar'
        assert fast_path_match(pattern, path) is True
        path = 'eureka/apps/foo/test/list/bar/'
        assert fast_path_match(pattern, path) is False
        path = 'eureka/apps/test/list'
        assert fast_path_match(pattern, path) is True
        path = 'eureka/test/list'
        assert fast_path_match(pattern, path) is False

        pattern = '/eureka/**/b/**/*.txt'
        path = '/eureka/a/aa/aaa/b/bb/bbb/xxxxxx.txt'
        assert fast_path_match(pattern, path) is True
        path = '/eureka/a/aa/aaa/b/bb/bbb/xxxxxx'
        assert fast_path_match(pattern, path) is False


if __name__ == '__main__':
    unittest.main()
