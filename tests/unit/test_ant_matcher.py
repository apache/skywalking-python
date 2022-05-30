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
        self.assertTrue(fast_path_match(pattern, path))
        path = '/eureka/'
        self.assertTrue(fast_path_match(pattern, path))
        path = '/eureka/apps/'
        self.assertFalse(fast_path_match(pattern, path))

        pattern = '/eureka/*/'
        path = '/eureka/apps/'
        self.assertTrue(fast_path_match(pattern, path))
        path = '/eureka/'
        self.assertFalse(fast_path_match(pattern, path))
        path = '/eureka/apps/list'
        self.assertFalse(fast_path_match(pattern, path))

        pattern = '/eureka/**'
        path = '/eureka/'
        self.assertTrue(fast_path_match(pattern, path))
        path = '/eureka/apps/test'
        self.assertTrue(fast_path_match(pattern, path))
        path = '/eureka/apps/test/'
        self.assertFalse(fast_path_match(pattern, path))

        pattern = 'eureka/apps/?'
        path = 'eureka/apps/list'
        self.assertFalse(fast_path_match(pattern, path))
        path = 'eureka/apps/'
        self.assertFalse(fast_path_match(pattern, path))
        path = 'eureka/apps/a'
        self.assertTrue(fast_path_match(pattern, path))

        pattern = 'eureka/**/lists'
        path = 'eureka/apps/lists'
        self.assertTrue(fast_path_match(pattern, path))
        path = 'eureka/apps/test/lists'
        self.assertTrue(fast_path_match(pattern, path))
        path = 'eureka/apps/test/'
        self.assertFalse(fast_path_match(pattern, path))
        path = 'eureka/apps/test'
        self.assertFalse(fast_path_match(pattern, path))

        pattern = 'eureka/**/test/**'
        path = 'eureka/apps/test/list'
        self.assertTrue(fast_path_match(pattern, path))
        path = 'eureka/apps/foo/test/list/bar'
        self.assertTrue(fast_path_match(pattern, path))
        path = 'eureka/apps/foo/test/list/bar/'
        self.assertFalse(fast_path_match(pattern, path))
        path = 'eureka/apps/test/list'
        self.assertTrue(fast_path_match(pattern, path))
        path = 'eureka/test/list'
        self.assertTrue(fast_path_match(pattern, path))

        pattern = 'eureka/*/**/test/**'
        path = 'eureka/test/list'
        self.assertFalse(fast_path_match(pattern, path))

        pattern = '/eureka/**/b/**/*.txt'
        path = '/eureka/a/aa/aaa/b/bb/bbb/xxxxxx.txt'
        self.assertTrue(fast_path_match(pattern, path))
        path = '/eureka/a/aa/aaa/b/bb/bbb/xxxxxx'
        self.assertFalse(fast_path_match(pattern, path))


if __name__ == '__main__':
    unittest.main()
