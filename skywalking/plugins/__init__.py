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
import pkg_resources

from packaging import version

from skywalking import config

import skywalking

logger = logging.getLogger(__name__)


def install():
    for importer, modname, ispkg in pkgutil.iter_modules(skywalking.plugins.__path__):
        disable_patterns = config.disable_plugins
        if isinstance(disable_patterns, str):
            disable_patterns = [re.compile(p.strip()) for p in disable_patterns.split(',') if p.strip()]
        else:
            disable_patterns = [re.compile(p.strip()) for p in disable_patterns if p.strip()]
        if any(pattern.match(modname) for pattern in disable_patterns):
            logger.info('plugin %s is disabled and thus won\'t be installed', modname)
            continue
        logger.debug('installing plugin %s', modname)
        plugin = importer.find_module(modname).load_module(modname)

        ok = pkg_version_check(plugin, modname)
        if not ok:
            continue

        if not hasattr(plugin, 'install') or inspect.ismethod(getattr(plugin, 'install')):
            logger.warning('no `install` method in plugin %s, thus the plugin won\'t be installed', modname)
            continue
        plugin.install()


_operators = {
    '<': lambda cv, ev: cv < ev,
    '<=': lambda cv, ev: cv < ev or cv == ev,
    '=': lambda cv, ev: cv == ev,
    '>=': lambda cv, ev: cv > ev or cv == ev,
    '>': lambda cv, ev: cv > ev,
    '!=': lambda cv, ev: cv != ev
}


def pkg_version_check(plugin, modname):
    ok = True

    if hasattr(plugin, "version_rule"):
        pkg_name = plugin.version_rule.get("name")
        rules = plugin.version_rule.get("rules")

        try:
            current_pkg_version = pkg_resources.get_distribution(pkg_name).version
        except pkg_resources.DistributionNotFound:
            ok = False
            logger.warning("plugin %s didn\'t find the corresponding package %s, thus won't be installed",
                           modname, pkg_name)
            return ok

        # check all rules
        for rule in rules:
            idx = 2 if rule[1] == '=' else 1
            symbol = rule[0:idx]
            expect_pkg_version = rule[idx:]

            current_version = version.parse(current_pkg_version)
            expect_version = version.parse(expect_pkg_version)
            f = _operators.get(symbol) or None

            # version rule parse error, take it as no more version rules and return True.
            if not f:
                logger.warning("plugin %s version rule %s error. only allow >,>=,=,<=,<,!= symbols", modname, rule)
                return ok

            if not f(current_version, expect_version):
                ok = False
                logger.warning("plugin %s need package %s version follow rules %s ,current version " +
                               "is %s, thus won\'t be installed", modname, pkg_name, str(rules), current_pkg_version)
                break

        return ok
    else:
        # no version rules was set, no checks
        return ok
