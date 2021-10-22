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
A management utility to handle testing matrix for different Pythons and Library versions
"""
import sys

from skywalking.utils.comparator import operators
from skywalking.utils.exception import VersionRuleException


def compare_version(rule_unit):
    idx = 2 if rule_unit[1] == '=' else 1
    symbol = rule_unit[0:idx]
    expect_python_version = tuple(map(int, rule_unit[idx:].split('.')))
    test_python_version = sys.version_info[:2]  # type: tuple
    f = operators.get(symbol) or None
    if not f:
        raise VersionRuleException(f'version rule {rule_unit} error. only allow >,>=,==,<=,<,!= symbols')

    return f(test_python_version, expect_python_version)


def get_test_vector(lib_name: str, support_matrix: dict):
    """
    If gets empty or ! will get skipped
    Args:
        support_matrix: a test matrix including python version specification and lib version
        lib_name: the name of the tested lib, used for requirements.txt generation

    Returns:

    """
    test_matrix = support_matrix[lib_name]
    for py_version in test_matrix:
        if compare_version(py_version):
            # proceed if current python version is valid
            version_row = test_matrix[py_version]
            return [f'{lib_name}=={idx}' for idx in version_row]
    return []  # non-match, CI will skip the test case for this version


if __name__ == '__main__':
    import pytest

    pytest.main(['-v', '../tests/'])
