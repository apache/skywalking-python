# FAQ

#### Q: How to disable some plugins?

#### A: You can find the plugin name in [the list](../README.md#supported-libraries) and disable one or more plugins by following methods.

```python
from skywalking import config

config.disable_plugins = ['sw_http_server', 'sw_urllib_request']  # can be also CSV format, i.e. 'sw_http_server,sw_urllib_request'
```

you can also disable the plugins via environment variables `SW_AGENT_DISABLE_PLUGINS`.

#### Q: How to build from sources?

#### A: Download the source tar from [the official website](http://skywalking.apache.org/downloads/), and run the following commands to build from source

```shell
$ tar -zxf skywalking-python-src-<version>.tgz
$ cd skywalking-python-src-<version>
$ make install
```

If you want to build from the latest source codes from GitHub, for some reasons, for example, you want to try the latest features that are not released yet, please clone the source codes from GitHub and `make install` it:

```shell
git clone https://github.com/apache/skywalking-python
cd skywalking-python
git submodule update --init
make install
``` 

**NOTE** that only releases from [the website](http://skywalking.apache.org/downloads/) are official Apache releases. 
