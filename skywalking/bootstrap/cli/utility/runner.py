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

""" User application command runner """
import logging
import os
import platform
import sys
from typing import List

from skywalking.bootstrap import cli_logger
from skywalking.bootstrap.cli import SWRunnerFailure


def execute(command: List[str]) -> None:
    """ Set up environ and invokes the given command to replace current process """

    cli_logger.debug(f'SkyWalking Python agent `runner` received command {command}')

    cli_logger.debug('Adding sitecustomize.py to PYTHONPATH')

    from skywalking.bootstrap.loader import __file__ as loader_dir

    loader_path = os.path.dirname(loader_dir)
    new_path = ''

    python_path = os.environ.get('PYTHONPATH')
    if python_path:  # If there is already a different PYTHONPATH, PREPEND to it as we must get loaded first.
        partitioned = python_path.split(os.path.pathsep)
        if loader_path not in partitioned:  # check if we are already there
            new_path = os.path.pathsep.join([loader_path, python_path])  # type: str

    # When constructing sys.path PYTHONPATH is always
    # before other paths and after interpreter invoker path, which is here or none
    os.environ['PYTHONPATH'] = new_path if new_path else loader_path
    cli_logger.debug(f"Updated PYTHONPATH - {os.environ['PYTHONPATH']}")

    # Used in sitecustomize to compare command's Python installation with CLI
    # If not match, need to stop agent from loading, and kill the process
    os.environ['SW_PYTHON_PREFIX'] = os.path.realpath(os.path.normpath(sys.prefix))
    os.environ['SW_PYTHON_VERSION'] = platform.python_version()

    # Pass down the logger debug setting to the replaced process, need a new logger there
    os.environ['SW_PYTHON_CLI_DEBUG_ENABLED'] = 'True' if cli_logger.level == logging.DEBUG else 'False'

    try:
        cli_logger.debug(f'New process starting with file - `{command[0]}` args - `{command}`')
        os.execvp(command[0], command)
    except OSError:
        raise SWRunnerFailure
