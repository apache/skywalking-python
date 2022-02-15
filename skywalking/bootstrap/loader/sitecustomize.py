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

""" This version of sitecustomize will
1. initializes the SkyWalking Python Agent.
2. invoke an existing sitecustomize.py.
Not compatible with Python <= 3.3

When executing commands with `sw-python run command`
This particular sitecustomize module will be picked up by any valid replacement
process(command) invoked by os.execvp in runner.py, thus will be seen by potentially
incompatible Python versions and system interpreters, which certainly will cause problems.
Therefore, an attempt to use command leading to a different Python interpreter should be stopped.
"""
import importlib
import logging
import os
import platform
import sys


def _get_sw_loader_logger():
    """ Setup a new logger with passed skywalking CLI env vars,
    don't import from skywalking, it may not be on sys.path
    if user misuses the CLI to run programs out of scope
    """
    from logging import getLogger
    logger = getLogger('skywalking-loader')
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(name)s [%(threadName)s] [%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.propagate = False
    if os.environ.get('SW_PYTHON_CLI_DEBUG_ENABLED') == 'True':  # set from the original CLI runner
        logger.setLevel(level=logging.DEBUG)
    return logger


_sw_loader_logger = _get_sw_loader_logger()
_sw_loader_logger_debug_enabled = _sw_loader_logger.isEnabledFor(logging.DEBUG)
# DEBUG messages in case execution goes wrong
if _sw_loader_logger_debug_enabled:
    _sw_loader_logger.debug('---------------sitecustomize.py---------------')
    _sw_loader_logger.debug(f'Successfully imported sitecustomize.py from `{__file__}`')
    _sw_loader_logger.debug(f'You are inside working dir - {os.getcwd()}')
    _sw_loader_logger.debug(f'Using Python version - {sys.version} ')
    _sw_loader_logger.debug(f'Using executable at - {sys.executable}')
    _sw_loader_logger.debug(f'System Base Python executable location {sys.base_prefix}')

if sys.prefix != sys.base_prefix:
    _sw_loader_logger.debug('[The SkyWalking agent bootstrapper is running inside a virtual environment]')

# It is possible that someone else also has a sitecustomize.py
# in sys.path either set by .pth files or manually, we need to run them as well
# The path to user sitecustomize.py is after ours in sys.path, needs to be imported here.
# just to be safe, remove loader thoroughly from sys.path and also sys.modules

cleared_path = [p for p in sys.path if p != os.path.dirname(__file__)]
sys.path = cleared_path  # remove this version from path
loaded = sys.modules.pop('sitecustomize', None)  # pop sitecustomize from loaded

# now try to find the original sitecustomize provided in user env
try:
    loaded = importlib.import_module('sitecustomie')
    _sw_loader_logger.debug(f'Found user sitecustomize file {loaded}, imported')
except ImportError:  # ModuleNotFoundError
    _sw_loader_logger.debug('Original sitecustomize module not found, skipping.')
finally:  # surprise the import error by adding loaded back
    sys.modules['sitecustomize'] = loaded

# This sitecustomize by default doesn't remove the loader dir from PYTHONPATH,
# Thus, subprocesses and multiprocessing also inherits this sitecustomize.py
# This behavior can be turned off using a user provided env below
# os.environ['SW_PYTHON_BOOTSTRAP_PROPAGATE']

if os.environ.get('SW_PYTHON_BOOTSTRAP_PROPAGATE') == 'False':
    if os.environ.get('PYTHONPATH'):
        partitioned = os.environ['PYTHONPATH'].split(os.path.pathsep)
        loader_path = os.path.dirname(__file__)
        if loader_path in partitioned:  # check if we are already removed by a third-party
            partitioned.remove(loader_path)
            os.environ['PYTHONPATH'] = os.path.pathsep.join(partitioned)
            _sw_loader_logger.debug('Removed loader from PYTHONPATH, spawned process will not have agent enabled')

# Note that users could be misusing the CLI to call a Python program that
# their Python env doesn't have SkyWalking installed. Or even call another
# env that has another version of SkyWalking installed, which is leads to problems.
# Even if `import skywalking` was successful, doesn't mean its the same one where sw-python CLI was run.
# Needs further checking for Python versions and prefix that passed down from CLI in os.environ.

cli_python_version = os.environ.get('SW_PYTHON_VERSION')
cli_python_prefix = os.environ.get('SW_PYTHON_PREFIX')

version_match = cli_python_version == platform.python_version()

# windows can sometimes make capitalized path, lower them can help
prefix_match = cli_python_prefix.lower() == os.path.realpath(os.path.normpath(sys.prefix)).lower()

if not (version_match and prefix_match):

    _sw_loader_logger.error(
        f'\nPython used by sw-python CLI - v{cli_python_version} at {cli_python_prefix}\n'
        f'Python used by your actual program - v{platform.python_version()} '
        f'at {os.path.realpath(os.path.normpath(sys.prefix))}'
    )
    _sw_loader_logger.error('The sw-python CLI was instructed to run a program '
                            'using an different Python installation '
                            'this is not safe and loader will not proceed. '
                            'Please make sure that sw-python cli, skywalking agent and your '
                            'application are using the same Python installation, '
                            'Rerun with debug flag, `sw-python -d run yourapp` for some troubleshooting information.'
                            'use `which sw-python` to find out the invoked CLI location')
    os._exit(1)  # do not go further

else:
    from skywalking import agent, config

    # also override debug for skywalking agent itself
    if os.environ.get('SW_PYTHON_CLI_DEBUG_ENABLED') == 'True':  # set from the original CLI runner
        config.logging_level = 'DEBUG'

    # Currently supports configs read from os.environ

    # This is for python 3.6 - 3.7(maybe) argv is not set for embedded interpreter thus will cause failure in
    # those libs that imports argv from sys, we need to set it manually if it's not there already
    # otherwise the plugin install will fail and things won't work properly, example - Sanic
    if not hasattr(sys, 'argv'):
        sys.argv = ['']

    # noinspection PyBroadException
    try:
        _sw_loader_logger.debug('SkyWalking Python Agent starting, loader finished.')
        agent.start()
    except Exception:
        _sw_loader_logger.exception('SkyWalking Python Agent failed to start, please inspect your package installation')
