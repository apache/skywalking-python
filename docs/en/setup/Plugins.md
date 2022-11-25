# Supported Libraries
This document is **automatically** generated from the SkyWalking Python testing matrix.

The column of versions only indicates the set of library versions tested in a best-effort manner.

If you find newer major versions that are missing from the following table, and it's not documented as a limitation,
please PR to update the test matrix in the plugin.

Versions marked as NOT SUPPORTED may be due to
an incompatible version with Python in the original library
or a limitation of SkyWalking auto-instrumentation (welcome to contribute!)

### Plugin Support Table
Library | Python Version - Lib Version | Plugin Name
| :--- | :--- | :--- |
| [aiohttp](https://docs.aiohttp.org) | Python >=3.7 - ['3.7.*'];  | `sw_aiohttp` |
| [aioredis](https://aioredis.readthedocs.io/) | Python >=3.7 - ['2.0.*'];  | `sw_aioredis` |
| [aiormq](https://pypi.org/project/aiormq/) | Python >=3.7 - ['6.3', '6.4'];  | `sw_aiormq` |
| [amqp](https://pypi.org/project/amqp/) | Python >=3.7 - ['2.6.1'];  | `sw_amqp` |
| [asyncpg](https://github.com/MagicStack/asyncpg) | Python >=3.7 - ['0.25.0'];  | `sw_asyncpg` |
| [bottle](http://bottlepy.org/docs/dev/) | Python >=3.7 - ['0.12.21'];  | `sw_bottle` |
| [celery](https://docs.celeryq.dev) | Python >=3.7 - ['5.1'];  | `sw_celery` |
| [confluent_kafka](https://www.confluent.io/) | Python >=3.7 - ['1.5.0', '1.7.0', '1.8.2'];  | `sw_confluent_kafka` |
| [django](https://www.djangoproject.com/) | Python >=3.7 - ['3.2'];  | `sw_django` |
| [elasticsearch](https://github.com/elastic/elasticsearch-py) | Python >=3.7 - ['7.13', '7.14', '7.15'];  | `sw_elasticsearch` |
| [hug](https://falcon.readthedocs.io/en/stable/) | Python >=3.10 - ['2.5', '2.6']; Python >=3.7 - ['2.4.1', '2.5', '2.6'];  | `sw_falcon` |
| [fastapi](https://fastapi.tiangolo.com) | Python >=3.7 - ['0.70.1'];  | `sw_fastapi` |
| [flask](https://flask.palletsprojects.com) | Python >=3.7 - ['2.0'];  | `sw_flask` |
| [http_server](https://docs.python.org/3/library/http.server.html) | Python >=3.7 - ['*'];  | `sw_http_server` |
| [werkzeug](https://werkzeug.palletsprojects.com/) | Python >=3.7 - ['1.0.1', '2.0'];  | `sw_http_server` |
| [kafka-python](https://kafka-python.readthedocs.io) | Python >=3.7 - ['2.0'];  | `sw_kafka` |
| [mysqlclient](https://mysqlclient.readthedocs.io/) | Python >=3.7 - ['2.1.0'];  | `sw_mysqlclient` |
| [psycopg[binary]](https://www.psycopg.org/) | Python >=3.7 - ['3.0'];  | `sw_psycopg` |
| [psycopg2-binary](https://www.psycopg.org/) | Python >=3.10 - NOT SUPPORTED YET; Python >=3.7 - ['2.9'];  | `sw_psycopg2` |
| [pymongo](https://pymongo.readthedocs.io) | Python >=3.7 - ['3.11.*'];  | `sw_pymongo` |
| [pymysql](https://pymysql.readthedocs.io/en/latest/) | Python >=3.7 - ['1.0'];  | `sw_pymysql` |
| [pyramid](https://trypyramid.com) | Python >=3.7 - ['1.10', '2.0'];  | `sw_pyramid` |
| [pika](https://pika.readthedocs.io) | Python >=3.7 - ['1.2'];  | `sw_rabbitmq` |
| [redis](https://github.com/andymccurdy/redis-py/) | Python >=3.7 - ['3.5'];  | `sw_redis` |
| [requests](https://requests.readthedocs.io/en/master/) | Python >=3.7 - ['2.26', '2.25'];  | `sw_requests` |
| [sanic](https://sanic.readthedocs.io/en/latest) | Python >=3.10 - NOT SUPPORTED YET; Python >=3.7 - ['20.12'];  | `sw_sanic` |
| [tornado](https://www.tornadoweb.org) | Python >=3.7 - ['6.0', '6.1'];  | `sw_tornado` |
| [urllib3](https://urllib3.readthedocs.io/en/latest/) | Python >=3.7 - ['1.26', '1.25'];  | `sw_urllib3` |
| [urllib_request](https://docs.python.org/3/library/urllib.request.html) | Python >=3.7 - ['*'];  | `sw_urllib_request` |
### Notes
- The celery server running with "celery -A ..." should be run with the HTTP protocol
as it uses multiprocessing by default which is not compatible with the gRPC protocol implementation
in SkyWalking currently. Celery clients can use whatever protocol they want.
