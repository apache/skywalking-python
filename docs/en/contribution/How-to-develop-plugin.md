## Plugin Development Guide

You can always take [the existing plugins](../setup/Plugins.md) as examples, while there are some general ideas for all plugins.
1. A plugin is a module under the directory `skywalking/plugins` with an `install` method; 
2. Inside the `install` method, you find out the relevant method(s) of the libraries that you plan to instrument, and create/close spans before/after those method(s).
3. You should also provide version rules in the plugin module, which means the version of package your plugin aim to test. 

   All below variables will be used by the tools/plugin_doc_gen.py to produce a latest [Plugin Doc](../setup/Plugins.md).

   ```python
   link_vector = ['https://www.python-httpx.org/']  # This should link to the official website/doc of this lib
   # The support matrix is for scenarios where some libraries don't work for certain Python versions
   # Therefore, we use the matrix to instruct the CI testing pipeline to skip over plugin test for such Python version
   # The right side versions, should almost always use A.B.* to test the latest minor version of two recent major versions. 
   support_matrix = {
       'httpx': {
           '>=3.7': ['0.23.*', '0.22.*']
       }
   }
   # The note will be used when generating the plugin documentation for users.
   note = """"""
   ```
4. Every plugin requires a corresponding test under `tests/plugin` before it can be merged, refer to the [Plugin Test Guide](How-to-test-plugin.md) when writing a plugin test.
5. Add the corresponding configuration options added/modified by the new plugin to the config.py and add new comments for each, then regenerate the `configuration.md` by `make doc-gen`.

## Steps after coding

If your PR introduces the need for a new non-standard library which needs to be pulled via pip or if it removes the need for a previously-used library:
1. Run `poetry add library --group plugins` to pin the dependency to the plugins group, **Do not add it to the main dependency!**
2. Run `make doc-gen` to generate a test matrix documentation for the plugin.