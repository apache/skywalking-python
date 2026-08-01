# How to use with Gunicorn?

Gunicorn is another popular process manager and prefork server widely used in production. 
The state-of-the-art practice is to use Gunicorn as the process manager for ASGI applications such as FastAPI to get resilient & blazing fast services.

Since Gunicorn is a prefork server, it will fork a new process for each worker, and the forked process will be the one that actually
serves requests.

> Tired of understanding these complicated multiprocessing behaviors? 
> Try the new `sw-python run --prefork/-p` support for Gunicorn first!
> You can always fall back to the manual approach (although it's also non-intrusive for application).

## Automatic Injection Approach (Non-intrusive)

> Note: Python 3.10+ is required. Earlier versions (3.7-3.9) are no longer supported.

**TL;DR:** specify `-p` or `--prefork` in `sw-python run -p` and every Gunicorn worker will get its own working agent (the master is instrumented only and runs no agent).

**Important:** if the call to gunicorn is prefixed with other commands, this approach will fail 
since agent currently looks for the command line input at index 0 for safety as an experimental feature.

```shell
sw-python run -p gunicorn gunicorn_consumer_prefork:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8088
```


**Long version:** (notice this is different from how uWSGI equivalent works)

By specifying the -p or --prefork option in sw-python CLI, the `agent_experimental_fork_support` agent option will be turned on automatically. 

Startup flow:
sw-python -> gunicorn -> master process (instrumentation only) -> fork -> worker process (full agent starts due to os.register_at_fork)

The master process does not run a full agent: it only installs instrumentation, and the reporters plus the
gRPC channel are created in each forked worker. Therefore the master does not appear as a service instance
(it takes no requests anyway). A gRPC channel created before fork() is unsafe with grpcio >= 1.80, see
[apache/skywalking#13958](https://github.com/apache/skywalking/issues/13958).

> A runnable example can be found in the demo folder of skywalking-python GitHub repository

### Known issue with agent <= 1.2.0 and grpcio >= 1.80

Agent versions up to 1.2.0 started a full agent (including a gRPC channel) in the Gunicorn master before forking.
With grpcio >= 1.80 this produces continuous `Kick Failure (eventfd_write: Bad file descriptor)` errors
and can silently hang workers. Tracing generally keeps working — the errors come from the gRPC client polling
engine and are unrelated to the OAP version. Workarounds on old agents: pin `grpcio<1.80` or use `SW_AGENT_PROTOCOL=http`.
Fixed agent versions require `grpcio >= 1.83` and never create a gRPC channel in the master.

### Incompatible with the asyncio enhancement

`SW_AGENT_ASYNCIO_ENHANCEMENT=true` is incompatible with `sw-python run -p gunicorn`: the asyncio agent has no
fork support, so the agent refuses to start (an error is logged) and the application serves WITHOUT observability.
Remove the asyncio enhancement option, or run Gunicorn without `-p`.

## Manual Approach (only use when sw-python doesn't work)

**Limitation**: Using normal postfork hook will not add observability to the master process.
Do NOT start an agent in the master process (e.g. from a prefork hook): a gRPC channel created before
fork() is unsafe with grpcio >= 1.80 and can deadlock workers.

The following is just an example, since Gunicorn's automatic injection approach is likely to work in many situations.

> The manual approach should not be used together with the agent's fork support. Otherwise, agent will be dual booted and 
> raise an error saying that you should not do so.

```Python-
# Usage explained here: https://docs.gunicorn.org/en/stable/settings.html#post-fork
bind = '0.0.0.0:8088'
workers = 3

def post_fork(server, worker):
    # Important: The import of skywalking should be inside the post_fork function
    import os
    from skywalking import agent, config
    # append pid-suffix to instance name
    # This must be done to distinguish instances if you give your instance customized names 
    # (highly recommended to identify workers)
    # Notice the -child(pid) part is required to tell the difference of each worker.
    agent_instance_name = f'<some_good_name>-child({os.getpid()})'

    config.init(agent_collector_backend_services='127.0.0.1:11800', 
                agent_name='your awesome service', agent_instance_name=agent_instance_name)

    agent.start()
```

Run Gunicorn normally without sw-python CLI:

```shell
gunicorn gunicorn_consumer_prefork:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8088
```