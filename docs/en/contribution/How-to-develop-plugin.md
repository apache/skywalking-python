## Plugin Development Guide

You can always take [the existing plugins](../setup/Plugins.md) as examples, while there are some general ideas for all plugins.
1. A plugin is a module under the directory `skywalking/plugins` with an `install` method; 
2. Inside the `install` method, you find out the relevant method(s) of the libraries that you plan to instrument, and create/close spans before/after those method(s).
3. You should also provide version rules in the plugin module, which means the version of package your plugin support. You should init a dict with keys `name` and `rules`. the `name` is your plugin's corresponding package's name, the `rules` is the version rules this package should follow.
   
   You can use >, >=, ==, <=, <, and != operators in rules. 
   
   The relation between rules element in the rules array is **OR**, which means the version of the package should follow at least one rule in rules array.
   
   You can set many version rules in one element of rules array, separate each other with a space character, the relation of rules in one rule element is **AND**, which means the version of package should follow all rules in this rule element.
   
   For example, below `version_rule` indicates that the package version of `django` should `>=2.0 AND <=2.3 AND !=2.2.1` OR `>3.0`.
   ```python
   version_rule = {
       "name": "django",
       "rules": [">=2.0 <=2.3 !=2.2.1", ">3.0"]
   }
   ```
4. Every plugin requires a corresponding test under `tests/plugin` before it can be merged, refer to the [Plugin Test Guide](How-to-test-plugin.md) when writing a plugin test.
5. Update the [Supported Plugin List](../setup/Plugins.md).
6. Add the environment variables to [Environment Variable list](../setup/EnvVars.md) if any.

## Steps after coding

If your PR introduces the need for a new non-standard library which needs to be pulled via pip or if it removes the need for a previously-used library:
1. Run `poetry add library --group plugins` to pin the dependency to the plugins group, **Do not add it to the main dependency!**
2. Run `make doc-gen` to generate a test matrix documentation for the plugin.