## Change Logs

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
