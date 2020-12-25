# FAQ

#### Q: How to disable some plugins?

#### A: You can find the plugin name in [the list](../README.md#supported-libraries) and disable one or more plugins by following methods.

```python
from skywalking import config

config.disable_plugins = ['sw_http_server', 'sw_urllib_request']  # can be also CSV format, i.e. 'sw_http_server,sw_urllib_request'
```

you can also disable the plugins via environment variables `SW_AGENT_DISABLE_PLUGINS`.

#### Q: How to build from sources?

#### A: If you want to build the SkyWalking Python Agent from source codes, for some reasons, for example, you want to try the latest features that're not released yet, please clone the source codes from GitHub and `make install` it:

```shell
git clone https://github.com/apache/skywalking-python
cd skywalking-python
git submodule update --init
make install
``` 

**NOTE** that if you download the source codes (`.tgz`) from our official website, simply run `make install` without `git submodule update --init` because the submodules are packaged in the tar.
