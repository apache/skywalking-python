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


def fast_path_match(pattern: str, path: str):
    return normal_match(pattern, 0, path, 0)


def normal_match(pat: str, p: int, var: str, s: int) -> bool:
    while p < len(pat):
        pc = pat[p]
        sc = safe_char_at(var, s)

        if pc == '*':
            p += 1

            if safe_char_at(pat, p) == '*':
                p += 1

                return multi_wildcard_match(pat, p, var, s)
            else:
                return wildcard_match(pat, p, var, s)

        if (pc == '?' and sc != '0' and sc != '/') or pc == sc:
            s += 1
            p += 1
            continue

        return False

    return s == len(var)


def wildcard_match(pat: str, p: int, var: str, s: int) -> bool:
    pc = safe_char_at(pat, p)

    while True:
        sc = safe_char_at(var, s)

        if sc == '/':

            if pc == sc:
                return normal_match(pat, p + 1, var, s + 1)

            return False

        if normal_match(pat, p, var, s) is False:
            if s >= len(var):
                return False

            s += 1
            continue

        return True


def multi_wildcard_match(pat: str, p: int, var: str, s: int) -> bool:
    if p >= len(pat) and s < len(var):
        return var[len(var) - 1] != '/'

    while True:
        if not normal_match(pat, p, var, s):
            if s >= len(var):
                return False

            s += 1
            continue

        return True


def safe_char_at(value: str, index: int) -> str:
    if index >= len(value):
        return '0'

    return value[index]
