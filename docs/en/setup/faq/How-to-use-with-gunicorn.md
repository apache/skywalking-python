# How to use with Gunicorn?

Gunicorn is another popular process manager and prefork server widely used in production. 
The state-of-the-art practice is to use Gunicorn as the process manager for ASGI applications such as FastAPI to get resilient & blazing fast services.

Since Gunicorn is a prefork server, it will fork a new process for each worker, and the forked process will be the one that actually
serves requests.

> Tired of understanding these complicated multiprocessing behaviors? 
> Try the new `sw-python run --prefork/-p` support for Gunicorn first!
> You can always fall back to the manual approach (although it's also non-intrusive for application).

## Automatic Injection Approach (Non-intrusive)

> Caveat: Although E2E test passes for Python3.7, 
> there's a small chance that this approach won't work on Python 3.7 if your application uses gPRC protocol AND subprocess AND fork together
> (you will immediately see service is not starting normally, not randomly breaking after)  
> This is due to an unfixed bug in gRPC core that leads to deadlock if Python 3.7 application involves subprocess (like debug mode). 
> You should upgrade to Python 3.8+ soon since the EOL is approaching on 2023 June 27th, 
> or fallback to manual approach should this case happen, or simply use HTTP/Kafka protocol.

**TL;DR:** specify `-p` or `--prefork` in `sw-python run -p` and all Gunicorn workers and master will get their own working agent.

**Important:** if the call to gunicorn is prefixed with other commands, this approach will fail 
since agent currently looks for the command line input at index 0 for safety as an experimental feature.

```shell
sw-python run -p gunicorn gunicorn_consumer_prefork:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8088
```


**Long version:** (notice this is different from how uWSGI equivalent works)

By specifying the -p or --prefork option in sw-python CLI, the `agent_experimental_fork_support` agent option will be turned on automatically. 

Startup flow:
sw-python -> gunicorn -> master process (agent starts) -> fork -> worker process (agent restarts due to os.register_at_fork)

The master process will get its own agent, although it won't report any trace, since obviously it doesn't take requests, 
it still reports metrics that is useful for debugging

> A runnable example can be found in the demo folder of skywalking-python GitHub repository

## Manual Approach (only use when sw-python doesn't work)

**Limitation**: Using normal postfork hook will not add observability to the master process, you could also define a prefork hook to
start an agent in the master process, with a instance name like `instance-name-master(<pid>)`

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