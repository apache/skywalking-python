# SkyWalking Python Agent Command-Line Interface(CLI)

In releases before 0.7.0, you would at least need to add the following lines to your applications to get the agent attached and running.  

```python
from skywalking import agent
agent.start()
```


Now the SkyWalking Python agent implements a command-line interface that can be utilized to attach the agent to your
awesome applications during deployment **without changing any application code**, 
just like the [SkyWalking Java Agent](https://github.com/apache/skywalking-java).

## Usage

Upon successful [installation of the SkyWalking Python agent via pip](Installation.md#from-pypi),
a command-line script `sw-python` is installed in your environment (virtual env preferred).

### The `run` option

Currently, the `sw-python` CLI provides a `run` option, which you can use to execute your applications
(either begins with the `python` command or Python-based programs like `gunicorn` on your path) 
just like you invoke them normally, plus a prefix, the following example demonstrates the usage.

If your previous command to run your gunicorn application is:

`gunicorn app.wsgi`

Please change it to:

`sw-python run gunicorn app.wsgi`

The SkyWalking Python agent will startup along with your application shortly.

Note that the command does work with multiprocessing and subprocess as long as the `PYTHONPATH` is inherited, 
please configure the environment variables configuration accordingly based on the general documentation.

When executing commands with `sw-python run command`, your command's Python interpreter will pick up the SkyWalking loader module.

It is not safe to attach SkyWalking Agent to those commands that resides in another Python installation 
because incompatible Python versions and mismatched SkyWalking versions can cause problems. 
Therefore, any attempt to pass a command that uses a different Python interpreter/ environment will not bring up 
SkyWalking Python Agent even if another SkyWalking Python agent is installed there(no matter the version), 
and will force exit with an error message indicating the reasoning.

#### Disabling child processes from starting new agents

Sometimes you don't actually need the agent to monitor anything in a child process.

If you do not need the agent to get loaded for application child processes, you can turn off the behavior by setting an environment variable.

`SW_PYTHON_BOOTSTRAP_PROPAGATE` to `False`

Note the auto bootstrap depends on the environment inherited by child processes, 
thus prepending a new sitecustomize path to or removing the loader path from the `PYTHONPATH` could prevent the agent from loading in a child process. 

### Configuring the agent 

You would normally want to provide additional configurations other than the default ones.

#### Through environment variables

The currently supported method is to provide the environment variables listed 
and explained in the [Environment Variables List](EnvVars.md).

#### Through a sw-config.yaml

Currently, only environment variable configuration is supported; an optional `yaml` configuration is to be implemented.

### Enabling CLI DEBUG mode

Note the CLI is a new feature that manipulates the Python interpreter bootstrap behaviour, there could be unsupported cases.

If you encounter unexpected problems, please turn on the DEBUG mode by adding the `-d` or `--debug` flag to your `sw-python` command, as shown below.

From: `sw-python run command`

To: `sw-python -d run command`

Please attach the debug logs to the [SkyWalking Issues](https://github.com/apache/skywalking/issues) section if you believe it is a bug,
[idea discussions](https://github.com/apache/skywalking/discussions) and [pull requests](https://github.com/apache/skywalking-python/pulls) are always welcomed.

#### Known limitations

1. The CLI may not work properly with arguments that involve double quotation marks in some shells.
2. The CLI and bootstrapper stdout logs could get messy in Windows shells.
