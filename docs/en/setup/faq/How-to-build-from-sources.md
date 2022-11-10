# How to build from sources?

**Download the source tar from the [official website](http://skywalking.apache.org/downloads/), 
and run the following commands to build from source**

**Make sure you have Python 3.7+ and the `python3` command available**

```shell
$ tar -zxf skywalking-python-src-<version>.tgz
$ cd skywalking-python-src-<version>
$ make install
```

If you want to build from the latest source codes from GitHub for some reasons, 
for example, you want to try the latest features that are not released yet, 
please clone the source codes from GitHub and `make install` it:

```shell
$ git clone https://github.com/apache/skywalking-python
$ cd skywalking-python
$ git submodule update --init
$ make install
``` 

**NOTE** that only releases from [the website](http://skywalking.apache.org/downloads/) are official Apache releases. 
