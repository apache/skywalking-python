# How to disable some plugins?

**You can find the plugin name in the [list](../Plugins.md) 
and disable one or more plugins by following methods.**

```python
from skywalking import config

config.disable_plugins = ['sw_http_server', 'sw_urllib_request']  # can be also CSV format, i.e. 'sw_http_server,sw_urllib_request'
```

You can also disable the plugins via environment variables `SW_AGENT_DISABLE_PLUGINS`, 
please check the [Environment Variables List](../EnvVars.md) for an explanation.
