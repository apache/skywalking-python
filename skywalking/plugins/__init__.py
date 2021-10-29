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
import inspect
import logging
import pkgutil
import re
import traceback

import pkg_resources
from packaging import version

import skywalking
from skywalking import config
from skywalking.loggings import logger
from skywalking.utils.comparator import operators
from skywalking.utils.exception import VersionRuleException


def install():
    disable_patterns = config.disable_plugins
    if isinstance(disable_patterns, str):
        disable_patterns = [re.compile(p.strip()) for p in disable_patterns.split(',') if p.strip()]
    else:
        disable_patterns = [re.compile(p.strip()) for p in disable_patterns if p.strip()]
    for importer, modname, _ispkg in pkgutil.iter_modules(skywalking.plugins.__path__):
        if any(pattern.match(modname) for pattern in disable_patterns):
            logger.info("plugin %s is disabled and thus won't be installed", modname)
            continue
        logger.debug('installing plugin %s', modname)
        plugin = importer.find_module(modname).load_module(modname)

        # todo: refactor the version checker, currently it doesn't really work as intended
        supported = pkg_version_check(plugin)
        if not supported:
            logger.debug("check version for plugin %s's corresponding package failed, thus "
                         "won't be installed", modname)
            continue

        if not hasattr(plugin, 'install') or inspect.ismethod(plugin.install):
            logger.warning("no `install` method in plugin %s, thus the plugin won't be installed", modname)
            continue

        # noinspection PyBroadException
        try:
            plugin.install()
            logger.debug('Successfully installed plugin %s', modname)
        except Exception:
            logger.warning('failed to install plugin %s', modname)
            traceback.print_exc() if logger.isEnabledFor(logging.DEBUG) else None


def pkg_version_check(plugin):
    supported = True

    # no version rules was set, no checks
    if not hasattr(plugin, 'version_rule'):
        return supported

    pkg_name = plugin.version_rule.get('name')
    rules = plugin.version_rule.get('rules')

    try:
        current_pkg_version = pkg_resources.get_distribution(pkg_name).version
    except pkg_resources.DistributionNotFound:
        # when failed to get the version, we consider it as supported.
        return supported

    current_version = version.parse(current_pkg_version)
    # pass one rule in rules (OR)
    for rule in rules:
        if rule.find(' ') == -1:
            if check(rule, current_version):
                return supported
        else:
            # have to pass all rule_uint in this rule (AND)
            rule_units = rule.split(' ')
            results = [check(unit, current_version) for unit in rule_units]
            if False in results:
                # check failed, try to check next rule
                continue
            else:
                return supported

    supported = False
    return supported


def check(rule_unit, current_version):
    idx = 2 if rule_unit[1] == '=' else 1
    symbol = rule_unit[0:idx]
    expect_pkg_version = rule_unit[idx:]

    expect_version = version.parse(expect_pkg_version)
    f = operators.get(symbol) or None
    if not f:
        raise VersionRuleException(f'version rule {rule_unit} error. only allow >,>=,==,<=,<,!= symbols')

    return f(current_version, expect_version)
