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


def prefork_handler(command: List[str]) -> None:
    """
    This handles the cases where pre-forking servers are EXPLICITLY used:
    - gunicorn
    - uwsgi
    This handler only covers many plain usages, there could be cases where
    gunicorn/uwsgi is loaded by other scripts and the envvars used here
    are lost in such flow. (Aka. not covered by this handler)
    """
    os.environ['prefork'] = ''
    if command[0] == 'gunicorn':
        # Maybe should also check 1: since there could be a command before gunicorn
        cli_logger.info('We noticed you are using Gunicorn, '
                        'agent will automatically start the SkyWalking Python Agent'
                        'in all child (worker) processes and the master.')
        os.environ['prefork'] = 'gunicorn'
    elif command[0] == 'uwsgi':
        cli_logger.info('We noticed you are using uWSGI, '
                        'agent will automatically add the following '
                        'environment variables to your uWSGI options (to ensure a functional Python agent): '
                        '--enable-threads --master. \n'
                        'We will also start the SkyWalking Python Agent in all child (worker) '
                        'processes except for the master.')

        if '--master' not in command[1:]:
            cli_logger.warning('No master process is specified, '
                               'agent will not start properly in workers, '
                               'automatically adding --master to your uwsgi command.')
            os.environ['UWSGI_MASTER'] = 'true'

        if '--enable-threads' not in command[1:]:
            ...
            cli_logger.warning('No --enable-threads is specified, '
                               'agent will not start properly in workers, '
                               'automatically adding --enable-threads to your uwsgi command.')
            os.environ['UWSGI_ENABLE_THREADS'] = 'true'

        # this sets the option --import to our custom uwsgidecorator.postfork() function
        # which is in loader/uw.py
        os.environ['prefork'] = 'uwsgi'

        # let's hope no one uses up all 4 env variables, shared-python-import
        # shared-import, shared-pyimport, shared-py-import all imports in all processes no matter lazy/lazy-apps
        def pick_env_var():
            for env_var in ['UWSGI_SHARED_PYTHON_IMPORT',
                            'UWSGI_SHARED_IMPORT',
                            'UWSGI_SHARED_PYIMPORT',
                            'UWSGI_SHARED_PY_IMPORT']:
                if env_var not in os.environ:
                    return env_var
            raise SWRunnerFailure('No available env variable slot for sw-python to inject postfork hook, '
                                  'agent will not start properly in workers, please unset one of your env variables or '
                                  'fall back to manual postfork hook with @postfork.')

        os.environ[pick_env_var()] = 'uwsgi_hook'


def execute(command: List[str], experimental_check_prefork: bool) -> None:
    """ Set up environ and invokes the given command to replace current process """

    cli_logger.debug(f'SkyWalking Python agent `runner` received command {command}')

    if experimental_check_prefork:
        cli_logger.info('Detected experimental prefork support flag, checking for pre-forking servers...')
        prefork_handler(command=command)

    cli_logger.debug('Adding sitecustomize.py to PYTHONPATH')

    from skywalking.bootstrap.loader import __file__ as loader_dir
    from skywalking.bootstrap.hooks import __file__ as hook_dir
    loader_path = os.path.dirname(loader_dir)
    hook_path = os.path.dirname(hook_dir)

    new_path: str = ''
    python_path = os.environ.get('PYTHONPATH')
    if python_path:  # If there is already a different PYTHONPATH, PREPEND to it as we must get loaded first.
        partitioned = python_path.split(os.path.pathsep)
        if loader_path not in partitioned:  # check if we are already there
            new_path = os.path.pathsep.join([loader_path, hook_path, python_path])

    # When constructing sys.path PYTHONPATH is always
    # before other paths and after interpreter invoker path, which is here or none
    os.environ['PYTHONPATH'] = new_path if new_path else os.path.pathsep.join([loader_path, hook_path])
    cli_logger.debug(f"Updated PYTHONPATH - {os.environ['PYTHONPATH']}")

    # Used in sitecustomize to compare command's Python installation with CLI
    # If not match, need to stop agent from loading, and kill the process
    os.environ['SW_PYTHON_PREFIX'] = os.path.realpath(os.path.normpath(sys.prefix))
    os.environ['SW_PYTHON_VERSION'] = platform.python_version()

    # Pass down the logger debug setting to the replaced process, need a new logger there
    os.environ['SW_AGENT_SW_PYTHON_CLI_DEBUG_ENABLED'] = 'True' if cli_logger.level == logging.DEBUG else 'False'

    try:
        cli_logger.info(f'New process starting with command - `{command[0]}` args - `{command}`')
        os.execvp(command[0], command)
    except OSError:
        raise SWRunnerFailure
