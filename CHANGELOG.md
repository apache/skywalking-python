## Change Logs

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
