# How to use with uWSGI?

[uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) is popular in the Python ecosystem. It is a lightweight, fast, and easy-to-use web server.

Since uWSGI is relatively old and offers multi-language support, it can get quite troublesome due to the usage of a system-level fork.

Some of the original discussion can be found here:
* [[Python] Apache Skywalking, flask uwsgi, no metrics send to server · Issue #6324 · apache/skywalking](https://github.com/apache/skywalking/issues/6324)
* [[Bug] skywalking-python not work with uwsgi + flask in master workers mode and threads mode · Issue #8566 · apache/skywalking](https://github.com/apache/skywalking/issues/8566)

> Tired of understanding these complicated multiprocessing behaviours? 
> Try the new `sw-python run --prefork/-p` support for uWSGI first!
> You can always fall back to the manual approach. 
> (although it's also possible to pass postfork hook without changing code, which is essentially how sw-python is implemented)

> Limitation: regardless of the approach used, uWSGI master process cannot be safely monitored. Since it doesn't take any requests, it is generally acceptable.
> Alternatively, you could switch to Gunicorn, where its master process can be monitored properly along with all child workers.

**Important**: The `--enable-threads` and `--master` option must be given to allow the usage of post_fork hooks and threading in workers. 
In the `sw-python` CLI, these two options will be automatically injected for you in addition to the post_fork hook.

## Automatic Injection Approach (Non-intrusive)
**TL;DR:** specify `-p` or `--prefork` in `sw-python run -p` and all uWSGI workers will get their own working agent.

**Important:** if the call to uwsgi is prefixed with other commands, this approach will fail 
since agent currently looks for the command line input at index 0 for safety as an experimental feature.

```shell
sw-python run -p uwsgi --die-on-term \
    --http 0.0.0.0:9090 \
    --http-manage-expect \
    --master --workers 2 \
    --enable-threads \
    --threads 2 \
    --manage-script-name \
    --mount /=flask_consumer_prefork:app
```

**Long version:** (notice this is different from how Gunicorn equivalent works)

By specifying the -p or --prefork option in sw-python CLI, a `uwsgi_hook` will be registered by the CLI by adding the environment variable
into one of ['UWSGI_SHARED_PYTHON_IMPORT', 'UWSGI_SHARED_IMPORT', 'UWSGI_SHARED_PYIMPORT', 'UWSGI_SHARED_PY_IMPORT']. uWSGI will then
import the module and start the agent in forked workers. 


Startup flow:
sw-python -> uwsgi -> master process (agent doesn't start here) -> fork -> worker process (agent starts due to post_fork hook)

The master process (which doesn't accept requests) currently does not get its own agent 
as it can not be safely started and handled by os.register_at_fork() handlers. 

> A runnable example can be found in the demo folder of skywalking-python GitHub repository

## Manual Approach (only use when sw-python doesn't work)

If you get some problems when using SkyWalking Python agent, you can try to use the following manual method to call [`@postfork`](https://uwsgi-docs.readthedocs.io/en/latest/PythonDecorators.html#uwsgidecorators.postfork), the low-level API of uWSGI to initialize the agent.

The following is an example of the use of uWSGI and flask.

**Important**: Never directly start the agent in the app, forked workers are unlikely to work properly (even if they do, it's out of luck)
you should either add the following postfork, or try our new experimental automatic startup through sw-python CLI (see above).


```
# main.py

# Note: The --master uwsgi flag must be on, otherwise the decorators will not be available to import
from uwsgidecorators import postfork

@postfork
def init_tracing():
    # Important: The import of skywalking must be inside the postfork function
    from skywalking import agent, config
    # append pid-suffix to instance name
    # This must be done to distinguish instances if you give your instance customized names 
    # (highly recommended to identify workers)
    # Notice the -child(pid) part is required to tell the difference of each worker.
    agent_instance_name = f'<some_good_name>-child({os.getpid()})'
    
    config.init(agent_collector_backend_services='127.0.0.1:11800', 
                agent_name='your awesome service', agent_instance_name=agent_instance_name)

    agent.start()

from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
```

Run uWSGI normally without sw-python CLI:

```shell
uwsgi --die-on-term \
    --http 0.0.0.0:5000 \
    --http-manage-expect \
    --master --workers 3 \
    --enable-threads \
    --threads 3 \
    --manage-script-name \
    --mount /=main:app
```