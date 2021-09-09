# Developers' Guide

## Steps to get an operational virtual environment:

1. `git clone https://github.com/apache/skywalking-python.git`
1. Run the script(`setup-linux.sh`, `setup-windows.ps1`) for your relevant OS to create a virtual environment folder in the project root
(*skywalking-python/venv*) and install all the necessary requirements
1. Set up your IDE to use the generated virtual environment of Python

## Developing a new plugin

You can always take [the existing plugins](../../../skywalking/plugins) as examples, while there are some general ideas for all plugins.
1. A plugin is a module under directory [`skywalking/plugins/`](../../../skywalking/plugins) with an `install` method; 
1. Inside the `install` method, you find out the relevant method(s) of the libraries that you plan to instrument, and create/close spans before/after those method(s).
1. You should also provide version rules in the plugin module, which means the version of package your plugin support. You should init a dict with keys `name` and `rules`. the `name` is your plugin's corresponding package's name, the `rules` is the version rules this package should follow.
   
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
1. Every plugin requires a corresponding test under [`tests/plugin`](../../../tests/plugin) before it can be merged, refer to [the plugin test guide](PluginTest.md) when writing a plugin test.
1. Update [the supported list](../setup/Plugins.md).
1. Add the environment variables to [the list](../setup/EnvVars.md) if any.

## Steps after coding

If your PR introduces the need for a new non-standard library which needs to be pulled via pip or if it removes the need for a previously-used library:
1. Execute the [`build_requirements` script](../../../tools/env/build_requirements_linux.sh) relevant to your OS.
1. Double check the `requirements.txt` file in the project root to ensure that the changes have been reflected. 
