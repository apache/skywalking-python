## FAQ

Q: How to disable some plugins?
A: You can find the plugin name in [the list](../README.md#supported-libraries) and disable one or more plugins by following methods.

```python
from skywalking import config

config.disable_plugins = ['sw_http_server', 'sw_urllib_request']  # can be also CSV format, i.e. 'sw_http_server,sw_urllib_request'
```

you can also disable the plugins via environment variables `SW_AGENT_DISABLE_PLUGINS`.
