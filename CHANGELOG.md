## Change Logs

### 1.1.0

- Feature:
  - Users now can specify the `SW_AGENT_ASYNCIO_ENHANCEMENT` environment variable to enable the performance enhancement with asyncio (#316)
  - Support printing Trace IDs (TID) to collected application logs (#323)

- Plugins:
  - Add neo4j plugin.(#312)
  - Add pulsar plugin.(#345)

- Fixes:
  - Fix unexpected 'No active span' IllegalStateError (#311)
  - **Tentative**: Set upper bound <=5.9.5 for psutil package due to test failure. (#326)
  - Remove `DeprecationWarning` from `pkg_resources` by replace it with `importlib_metadata` (#329)
  - Fix unexpected 'decode' AttributeError when MySQLdb module is mapped by PyMySQL (#336)

### 1.0.1

- Feature:
  - Add a new workflow to push docker images for arm64 and amd64 (#297)

- Plugins:
  - Optimize loguru reporter plugin.(#302)

- Fixes:
  - Fix sw8 loss when use aiohttp (#299, issue#10669)
  - **Critical**: Fix a bug that leads to high cpu usage (#300, issue#10672)

- Others:
  - Use Kraft mode in E2E Kafka reporter tests (#303)

### 1.0.0

- **Important Note and Breaking Changes:**
  - **BREAKING**: Python 3.6 is no longer supported and may not function properly, Python 3.11 support is added and tested.
  - **BREAKING**: A number of common configuration options and environment variables are renamed to follow the convention of Java agent,
  please check with the latest official documentation before upgrading. (#273, #282)
  https://skywalking.apache.org/docs/skywalking-python/v1.0.0/en/setup/configuration/
  - **BREAKING**: All agent core capabilities are now covered by test cases and enabled by default (Trace, Log, PVM runtime metrics, Profiler)
  - **BREAKING**: DockerHub Python agent images since v1.0.0 will no longer include the `run` part in `ENTRYPOINT ["sw-python", "run"]`, 
  user should prefix their command with `[-d/--debug] run [-p/--prefork] <Command>` for extra flexibility.
  - Packaged wheel now provides a extra [all] option to support all three report protocols

- Feature:
  - Add support for Python 3.11 (#285)
  - Add MeterReportService (gRPC, Kafka reporter) (default:enabled) (#231, #236, #241, #243)
  - Add reporter for PVM runtime metrics (default:enabled) (#238, #247)
  - Add Greenlet profiler (#246)
  - Add test and support for Python Slim base images (#249)
  - Add support for the tags of Virtual Cache for Redis (#263)
  - Add a new configuration `kafka_namespace` to prefix the kafka topic names (#277)
  - Add log reporter support for loguru (#276)
  - Add **experimental** support for explicit os.fork(), restarts agent in forked process (#286)
  - Add **experimental** sw-python CLI `sw-python run [-p]` flag (-p/--prefork) to enable non-intrusive uWSGI and Gunicorn postfork support (#288)

- Plugins:
  - Add aioredis, aiormq, amqp, asyncpg, aio-pika, kombu RMQ plugins (#230 Missing test coverage) 
  - Add Confluent Kafka plugin (#233 Missing test coverage) 
  - Add HBase plugin Python HappyBase model  (#266) 
  - Add FastAPI plugin websocket protocol support (#269)
  - Add Websockets (client) plugin (#269)
  - Add HTTPX plugin (#283)

- Fixes:
  - Allow RabbitMQ BlockingChannel.basic_consume() to link with outgoing spans (#224)
  - Fix RabbitMQ basic_get bug (#225, #226)
  - Fix case when tornado socket name is None (#227)
  - Fix misspelled text "PostgreSLQ" -> "PostgreSQL" in Postgres-related plugins (#234)
  - Make sure `span.component` initialized as Unknown rather than 0 (#242)
  - Ignore websocket connections inside fastapi temporarily (#244, issue#9724)
  - Fix Kafka-python plugin SkyWalking self reporter ignore condition (#249)
  - Add primary endpoint in tracing context and endpoint info to log reporter (#261)
  - Enforce tag class type conversion (#262)
  - Fix sw_logging (log reporter) potentially throw exception leading to traceback confusion (#267)
  - Avoid reporting meaningless tracecontext with logs when there's no active span, UI will now show empty traceID (#272)
  - Fix exception handler in profile_context (#273)
  - Add namespace suffix to service name (#275)
  - Add periodical instance property report to prevent data loss (#279)
  - Fix sw_logging when `Logger.disabled` is true (#281)

- Docs:
  - New documentation on how to test locally (#222)
  - New documentation on the newly added meter reporter feature (#240)
  - New documentation on the newly added greenlet profiler and the original threading profiler (#250)
  - Overhaul documentation on development setup and testing (#249)
  - Add tables to state currently supported features of Python agent. (#271)
  - New configuration documentation generator (#273) 

- Others:
  - Pin CI SkyWalking License Eye (#221)
  - Fix dead link due to the 'next' url change (#235)
  - Pin CI SkyWalking Infra-E2E (#251)
  - Sync OAP, SWCTL versions in E2E and fix test cases (#249)
  - Overhaul development flow with Poetry (#249)
  - Fix grpcio-tools generated message type (#253)
  - Switch plugin tests to use slim Python images (#268)
  - Add unit tests to sw_filters (#269)

### 0.8.0
- Feature:
  - Update mySQL plugin to support two different parameter keys. (#186)
  - Add a `SW_AGENT_LOG_REPORTER_SAFE_MODE` option to control the HTTP basic auth credential filter (#200)

- Plugins:
  - Add Psycopg(3.x) support (#168)
  - Add MySQL support (#178)
  - Add FastAPI support (#181)
  - Drop support for flask 1.x due to dependency issue in Jinja2 and EOL (#195)
  - Add Bottle support (#214)

- Fixes:
  - Spans now correctly reference finished parents (#161)
  - Remove potential password leak from Aiohttp outgoing url (#175)
  - Handle error when REMOTE_PORT is missing in Flask (#176)
  - Fix sw-rabbitmq TypeError when there are no headers (#182)
  - Fix agent bootstrap traceback not shown in sw-python CLI (#183)
  - Fix local log stack depth overridden by agent log formatter (#192)
  - Fix typo that cause user sitecustomize.py not loaded (#193)
  - Fix instance property wrongly shown as UNKNOWN in OAP (#194)
  - Fix multiple components inconsistently named on SkyWalking UI (#199)
  - Fix SW_AGENT_LOGGING_LEVEL not properly set during startup (#196)
  - Unify the http tag name with other agents (#208)
  - Remove namespace to instance properties and add pid property (#205)
  - Fix the properties are not set correctly (#198)
  - Improved ignore path regex (#210)
  - Fix sw_psycopg2 register_type() (#211)
  - Fix psycopg2 register_type() second arg default (#212)
  - Enhance Traceback depth (#206)
  - Set spans whose http code > 400 to error (#187)

- Docs:
  - Add a FAQ doc on `how to use with uwsgi` (#188)

- Others:
  - Refactor current Python agent docs to serve on SkyWalking official website (#162)
  - Refactor SkyWalking Python to use the CLI for CI instead of legacy setup (#165)
  - Add support for Python 3.10 (#167)
  - Move flake configs all together (#169)
  - Introduce another set of flake8 extensions (#174)
  - Add E2E test coverage for trace and logging (#199)
  - Now Log reporter `cause_exception_depth` traceback limit defaults to 10
  - Enable faster CI by categorical parallelism (#170)

### 0.7.0

- Feature:
    - Support collecting and reporting logs to backend (#147)
    - Support profiling Python method level performance (#127
    - Add a new `sw-python` CLI that enables agent non-intrusive integration (#156)
    - Add exponential reconnection backoff strategy when OAP is down (#157)
    - Support ignoring traces by http method (#143)
    - `NoopSpan` on queue full, propagation downstream (#141)
    - Support agent namespace. (#126)
    - Support secure connection option for GRPC and HTTP (#134)

- Plugins:
    - Add Falcon Plugin (#146)
    - Update `sw_pymongo.py` to be compatible with cluster mode (#150)
    - Add Python celery plugin (#125)
    - Support tornado5+ and tornado6+ (#119)

- Fixes:
    - Remove HTTP basic auth credentials from log, stacktrace, segment (#152)
    - Fix `@trace` decorator not work (#136)
    - Fix grpc disconnect, add `SW_AGENT_MAX_BUFFER_SIZE` to control buffer queue size (#138)

- Others:
    - Chore: bump up `requests` version to avoid license issue (#142)
    - Fix module wrapt as normal install dependency (#123)
    - Explicit component inheritance (#132)
    - Provide dockerfile & images for easy integration in containerized scenarios (#159)

### 0.6.0

- Fixes:
    - Segment data loss when gRPC timing out. (#116)
    - `sw_tornado` plugin async handler status set correctly. (#115)
    - `sw_pymysql` error when connection haven't db. (#113)

### 0.5.0

- New plugins
    - Pyramid Plugin (#102)
    - AioHttp Plugin (#101)
    - Sanic Plugin (#91)

- API and enhancements
    - `@trace` decorator supports `async` functions
    - Supports async task context
    - Optimized path trace ignore
    - Moved exception check to `Span.__exit__`
    - Moved Method & Url tags before requests

- Fixes:
    - `BaseExceptions` not recorded as errors
    - Allow pending data to send before exit
    - `sw_flask` general exceptions handled
    - Make `skywalking` logging Non-global

- Chores and tests
    - Make tests really run on specified Python version
    - Deprecate 3.5 as it's EOL

### 0.4.0

- Feature: Support Kafka reporter protocol (#74)
- BugFix: Move generated packages into `skywalking` namespace to avoid conflicts (#72)
- BugFix: Agent cannot reconnect after server is down (#79)
- Test: Mitigate unsafe yaml loading (#76)

### 0.3.0

- New plugins
    - Urllib3 Plugin (#69)
    - Elasticsearch  Plugin (#64)
    - PyMongo Plugin (#60)
    - Rabbitmq Plugin (#53)
    - Make plugin compatible with Django (#52)

- API
    - Add process propagation (#67)
    - Add tags to decorators (#65)
    - Add Check version of packages when install plugins (#63)
    - Add thread propagation (#62)
    - Add trace ignore (#59)
    - Support snapshot context (#56)
    - Support correlation context (#55)

- Chores and tests
    - Test: run multiple versions of supported libraries (#66)
    - Chore: add pull request template for plugin (#61)
    - Chore: add dev doc and reorganize the structure (#58)
    - Test: update test health check (#57)
    - Chore: add make goal to package release tar ball (#54)



### 0.2.0

- New plugins
    - Kafka Plugin (#50)
    - Tornado Plugin (#48)
    - Redis Plugin (#44)
    - Django Plugin (#37)
    - PyMsql Plugin (#35)
    - Flask plugin (#31)

- API
    - Add ignore_suffix Config (#40)
    - Add missing `log` method and simplify test codes (#34)
    - Add content equality of SegmentRef (#30)
    - Validate carrier before using it (#29)

- Chores and tests
    - Test: print the diff list when validation failed (#46)
    - Created venv builders for linux/windows and req flashers + use documentation (#38)

### 0.1.0

- API: agent core APIs, check [the APIs and the examples](https://github.com/apache/skywalking-python/blob/3892cab9d5d2c03107cfb2b1c59a6c77c5c3cc35/README.md#api)
- Plugin: built-in libraries `http`, `urllib.request` and third-party library `requests` are supported.
- Test: agent test framework is setup, and the corresponding tests of aforementioned plugins are also added.
