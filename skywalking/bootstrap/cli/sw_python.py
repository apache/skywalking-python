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

""" This module is installed during package setup """
import argparse
import logging

from skywalking.bootstrap import cli_logger
from skywalking.bootstrap.cli import SWRunnerFailure
from skywalking.bootstrap.cli.utility import runner

_options = {
    'run': runner,
}


def start() -> None:
    """ Entry point of CLI """
    parser = argparse.ArgumentParser(description='SkyWalking Python Agent CLI',
                                     epilog='Append your command, with SkyWalking agent attached for you automatically',
                                     allow_abbrev=False)

    parser.add_argument('-d', '--debug', help='Print CLI debug logs to stdout', action='store_true')

    base_subparser = argparse.ArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(dest='option', required=True, help='CLI options, now only supports `run`, for '
                                                                          'help please type `sw-python -h` or refer '
                                                                          'to the CLI documentation')

    run_parser = subparsers.add_parser('run', parents=[base_subparser])

    # TODO support parsing optional sw_config.toml
    # config_parser = subparsers.add_parser("config", parents=[base_subparser])
    # parser.add_argument('-config', nargs='?', type=argparse.FileType('r'),
    #                     help='Optionally takes a sw_python.toml config file')

    run_parser.add_argument('-p', '--prefork', help='[Experimental] This flag turns on auto detection of '
                                                    'uwsgi and gunicorn, '
                                                    'then automatically starts the Python agent in each worker process.'
                                                    "(TL;DR: You don't need to add manual "
                                                    '@postfork hook to your app anymore)',
                            action='store_true')
    # The command arg compress all remaining args into itself
    # This must be the last arg
    run_parser.add_argument('command', help='Your original commands e.g. gunicorn app.wsgi',
                            nargs=argparse.REMAINDER, metavar='command')

    # To handle cases with flags and positional args in user commands
    args = parser.parse_args()  # type: argparse.Namespace

    cli_logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    cli_logger.debug(f'Args received {args}')

    if not args.command:
        cli_logger.error('Command is not provided, please type `sw-python -h` for the list of command line arguments')
        return
    try:
        dispatch(args)
    except SWRunnerFailure:
        cli_logger.exception(f"Failed to run the given user application command `{' '.join(args.command)}`, "
                             f'please make sure given command is valid.')
        return


def dispatch(args: argparse.Namespace) -> None:
    """ Dispatches parsed args to a worker """
    cli_option, actual_command = args.option, args.command

    cli_logger.debug(f"SkyWalking Python agent with CLI option '{cli_option}' and command {actual_command}")

    # Dispatch actual user application command to runner
    _options[cli_option].execute(command=actual_command, experimental_check_prefork=args.prefork)
