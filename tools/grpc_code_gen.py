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
import glob
import os
import re

import pkg_resources
from grpc_tools import protoc
from packaging import version

grpc_tools_version = pkg_resources.get_distribution('grpcio-tools').version
dest_dir = 'skywalking/protocol'
src_dir = 'protocol'


def touch(filename):
    open(filename, 'a').close()


def codegen():
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)

    touch(os.path.join(dest_dir, '__init__.py'))
    protoc_args = [
        'grpc_tools.protoc',
        f'--proto_path={src_dir}',
        f'--python_out={dest_dir}',
        f'--grpc_python_out={dest_dir}'
    ]
    if version.parse(grpc_tools_version) >= version.parse('1.49.0'):
        # https://github.com/grpc/grpc/issues/31247
        protoc_args += [f'--pyi_out={dest_dir}']
    protoc_args += list(glob.iglob(f'{src_dir}/**/*.proto'))
    protoc.main(protoc_args)

    for py_file in glob.iglob(os.path.join(dest_dir, '**/*.py')):
        touch(os.path.join(os.path.dirname(py_file), '__init__.py'))
        with open(py_file, 'r+') as file:
            code = file.read()
            file.seek(0)
            file.write(re.sub(r'from (.+) (import .+_pb2.*)', 'from ..\\1 \\2', code))
            file.truncate()


if __name__ == '__main__':
    codegen()
