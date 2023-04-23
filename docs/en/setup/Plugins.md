# Supported Libraries
This document is **automatically** generated from the SkyWalking Python testing matrix.

The column of versions only indicates the set of library versions tested in a best-effort manner.

If you find newer major versions that are missing from the following table, and it's not documented as a limitation,
please PR to update the test matrix in the plugin.

Versions marked as NOT SUPPORTED may be due to
an incompatible version with Python in the original library
or a limitation of SkyWalking auto-instrumentation (welcome to contribute!)

### Plugin Support Table
| Library | Python Version - Lib Version | Plugin Name |
| :--- | :--- | :--- |
| [aiohttp](https://docs.aiohttp.org) | Python >=3.7 - ['3.7.*'];  | `sw_aiohttp` |
| [aioredis](https://aioredis.readthedocs.io/) | Python >=3.7 - ['2.0.*'];  | `sw_aioredis` |
| [aiormq](https://pypi.org/project/aiormq/) | Python >=3.7 - ['6.3', '6.4'];  | `sw_aiormq` |
| [amqp](https://pypi.org/project/amqp/) | Python >=3.7 - ['2.6.1'];  | `sw_amqp` |
| [asyncpg](https://github.com/MagicStack/asyncpg) | Python >=3.7 - ['0.25.0'];  | `sw_asyncpg` |
| [bottle](http://bottlepy.org/docs/dev/) | Python >=3.7 - ['0.12.23'];  | `sw_bottle` |
| [celery](https://docs.celeryq.dev) | Python >=3.7 - ['5.1'];  | `sw_celery` |
| [confluent_kafka](https://www.confluent.io/) | Python >=3.7 - ['1.5.0', '1.7.0', '1.8.2'];  | `sw_confluent_kafka` |
| [django](https://www.djangoproject.com/) | Python >=3.7 - ['3.2'];  | `sw_django` |
| [elasticsearch](https://github.com/elastic/elasticsearch-py) | Python >=3.7 - ['7.13', '7.14', '7.15'];  | `sw_elasticsearch` |
| [hug](https://falcon.readthedocs.io/en/stable/) | Python >=3.11 - NOT SUPPORTED YET; Python >=3.10 - ['2.5', '2.6']; Python >=3.7 - ['2.4.1', '2.5', '2.6'];  | `sw_falcon` |
| [fastapi](https://fastapi.tiangolo.com) | Python >=3.7 - ['0.89.*', '0.88.*'];  | `sw_fastapi` |
| [flask](https://flask.palletsprojects.com) | Python >=3.7 - ['2.0'];  | `sw_flask` |
| [happybase](https://happybase.readthedocs.io) | Python >=3.7 - ['1.2.0'];  | `sw_happybase` |
| [http_server](https://docs.python.org/3/library/http.server.html) | Python >=3.7 - ['*'];  | `sw_http_server` |
| [werkzeug](https://werkzeug.palletsprojects.com/) | Python >=3.7 - ['1.0.1', '2.0'];  | `sw_http_server` |
| [httpx](https://www.python-httpx.org/) | Python >=3.7 - ['0.23.*', '0.22.*'];  | `sw_httpx` |
| [kafka-python](https://kafka-python.readthedocs.io) | Python >=3.7 - ['2.0'];  | `sw_kafka` |
| [loguru](https://pypi.org/project/loguru/) | Python >=3.7 - ['0.6.0', '0.7.0'];  | `sw_loguru` |
| [mysqlclient](https://mysqlclient.readthedocs.io/) | Python >=3.7 - ['2.1.*'];  | `sw_mysqlclient` |
| [psycopg[binary]](https://www.psycopg.org/) | Python >=3.11 - ['3.1.*']; Python >=3.7 - ['3.0.18', '3.1.*'];  | `sw_psycopg` |
| [psycopg2-binary](https://www.psycopg.org/) | Python >=3.10 - NOT SUPPORTED YET; Python >=3.7 - ['2.9'];  | `sw_psycopg2` |
| [pymongo](https://pymongo.readthedocs.io) | Python >=3.7 - ['3.11.*'];  | `sw_pymongo` |
| [pymysql](https://pymysql.readthedocs.io/en/latest/) | Python >=3.7 - ['1.0'];  | `sw_pymysql` |
| [pyramid](https://trypyramid.com) | Python >=3.7 - ['1.10', '2.0'];  | `sw_pyramid` |
| [pika](https://pika.readthedocs.io) | Python >=3.7 - ['1.2'];  | `sw_rabbitmq` |
| [redis](https://github.com/andymccurdy/redis-py/) | Python >=3.7 - ['3.5.*', '4.5.1'];  | `sw_redis` |
| [requests](https://requests.readthedocs.io/en/master/) | Python >=3.7 - ['2.26', '2.25'];  | `sw_requests` |
| [sanic](https://sanic.readthedocs.io/en/latest) | Python >=3.10 - NOT SUPPORTED YET; Python >=3.7 - ['20.12'];  | `sw_sanic` |
| [tornado](https://www.tornadoweb.org) | Python >=3.7 - ['6.0', '6.1'];  | `sw_tornado` |
| [urllib3](https://urllib3.readthedocs.io/en/latest/) | Python >=3.7 - ['1.26', '1.25'];  | `sw_urllib3` |
| [urllib_request](https://docs.python.org/3/library/urllib.request.html) | Python >=3.7 - ['*'];  | `sw_urllib_request` |
| [websockets](https://websockets.readthedocs.io) | Python >=3.7 - ['10.3', '10.4'];  | `sw_websockets` |
### Notes
- The celery server running with "celery -A ..." should be run with the HTTP protocol
as it uses multiprocessing by default which is not compatible with the gRPC protocol implementation
in SkyWalking currently. Celery clients can use whatever protocol they want.
- While Falcon is instrumented, only Hug is tested.
Hug is believed to be abandoned project, use this plugin with a bit more caution.
Instead of Hug, plugin test should move to test actual Falcon.
- The websocket instrumentation only traces client side connection handshake,
the actual message exchange (send/recv) is not traced since injecting headers to socket message
body is the only way to propagate the trace context, which requires customization of message structure
and extreme care. (Feel free to add this feature by instrumenting the send/recv methods commented out in the code
by either injecting sw8 headers or propagate the trace context in a separate message)

