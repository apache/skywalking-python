# SkyWalking Python Agent Command Line Interface (sw-python CLI)

**Now, SkyWalking Python Agent CLI is the recommended way of running your application with Python agent, 
the CLI is well-tested and used by all agent E2E & Plugin tests.**


In releases before 0.7.0, you would at least need to add the following lines to your applications to get the agent attached and running, 
this can be tedious in many cases due to large number of services, DevOps practices and can cause problem when used with prefork servers.

```python
from skywalking import agent, config
config.init(SomeConfig)
agent.start()
```


The SkyWalking Python agent implements a command-line interface that can be utilized to attach the agent to your
awesome applications during deployment **without changing any application code**, 
just like the [SkyWalking Java Agent](https://github.com/apache/skywalking-java).

> The following feature is added in v1.0.0 as experimental flag, so you need to specify the -p flag to `sw-python run -p`. 
> In the future, this flag will be removed and agent will automatically enable prefork/fork support in a more comprehensive manner.

Especially with the new automatic postfork injection feature, you no longer have to worry about threading and forking incompatibility.

Check [How to use with uWSGI](faq/How-to-use-with-uwsgi.md) and [How to use with Gunicorn](faq/How-to-use-with-gunicorn.md) to understand
the detailed background on what is post_fork, why you need them and how to easily overcome the trouble with `sw-python` CLI.

You should still read the [legacy way](Intrusive.md) to integrate agent in case the `sw-python` CLI is not working for you.



## Usage

Upon successful [installation of the SkyWalking Python agent via pip](Installation.md#from-pypi),
a command-line script `sw-python` is installed in your environment (virtual env preferred).

> run `sw-python` to see if it is available, you will need to pass configuration by environment variables.

For example: `export SW_AGENT_COLLECTOR_BACKEND_SERVICES=localhost:11800`

### The `run` option

The `sw-python` CLI provides a `run` option, which you can use to execute your applications
(either begins with the `python` command or Python-based programs like `gunicorn` on your path) 
just like you invoke them normally, plus a prefix, the following example demonstrates the usage.

If your previous command to run your gunicorn/uwsgi application is:

`gunicorn your_app:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8088`

or

`uwsgi --die-on-term --http 0.0.0.0:5000 --http-manage-expect --master --workers 3 --enable-threads --threads 3 --manage-script-name --mount /=main:app`

Please change it to (**the `-p` option starts one agent in each process, which is the correct behavior**):

**Important:** if the call to uwsgi/gunicorn is prefixed with other commands, this approach will fail 
since agent currently looks for the command line input at index 0 for safety as an experimental feature.

`sw-python run -p gunicorn your_app:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8088`

or 

`sw-python run -p uwsgi --die-on-term --http 0.0.0.0:5000 --http-manage-expect --master --workers 3 --enable-threads --threads 3 --manage-script-name --mount /=main:app`


The SkyWalking Python agent will start up along with all your application workers shortly.

Note that `sw-python` also work with spawned subprocess (os.exec*/subprocess) as long as the `PYTHONPATH` is inherited. 

Additionally, `sw-python` started agent works well with `os.fork` when your application forks workers, 
as long as the `SW_AGENT_EXPERIMENTAL_FORK_SUPPORT` is turned on. (It will be automatically turned on when gunicorn is detected)

## Configuring the agent 

You would normally want to provide additional configurations other than the default ones.

#### Through environment variables

The currently supported method is to provide the environment variables listed 
and explained in the [Environment Variables List](Configuration.md).

#### Through a sw-config.toml (TBD)

Currently, only environment variable configuration is supported; an optional `toml` configuration is to be implemented.

## Enabling CLI DEBUG mode

Note the CLI is a feature that manipulates the Python interpreter bootstrap behaviour, there could be unsupported cases.

If you encounter unexpected problems, please turn on the DEBUG mode by adding the `-d` or `--debug` flag to your `sw-python` command, as shown below.

From: `sw-python run command`

To: `sw-python -d run command`

Please attach the debug logs to the [SkyWalking Issues](https://github.com/apache/skywalking/issues) section if you believe it is a bug,
[idea discussions](https://github.com/apache/skywalking/discussions) and [pull requests](https://github.com/apache/skywalking-python/pulls) are always welcomed.


## Additional Remarks

When executing commands with `sw-python run command`, your command's Python interpreter will pick up the SkyWalking loader module.

It is not safe to attach SkyWalking Agent to those commands that resides in another Python installation 
because incompatible Python versions and mismatched SkyWalking versions can cause problems. 
Therefore, any attempt to pass a command that uses a different Python interpreter/ environment will not bring up 
SkyWalking Python Agent even if another SkyWalking Python agent is installed there(no matter the version), 
and will force exit with an error message indicating the reasoning.

#### Disabling spawned processes from starting new agents

Sometimes you don't actually need the agent to monitor anything in a new process (when it's not a web service worker). 
(here we mean process spawned by subprocess and os.exec*(), os.fork() is not controlled by this flag but `experimental_fork_support`)

If you do not need the agent to get loaded for application child processes, you can turn off the behavior by setting an environment variable.

`SW_AGENT_SW_PYTHON_BOOTSTRAP_PROPAGATE` to `False`

Note the auto bootstrap depends on the environment inherited by child processes, 
thus prepending a new sitecustomize path to or removing the loader path from the `PYTHONPATH` could also prevent the agent from loading in a child process. 

#### Known limitations

1. The CLI may not work properly with arguments that involve double quotation marks in some shells.
2. The CLI and bootstrapper stdout logs could get messy in Windows shells.
