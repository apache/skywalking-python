# # -*- coding:utf-8 -*-
# # author：huawei
#
# import os
# import time
# from functools import wraps
# from multiprocessing import Process
# from multiprocessing.process import BaseProcess
#
# import requests
#
# from skywalking.trace.context import get_context
#
# from skywalking import agent, config
# from skywalking.trace.tags import Tag
#
# origin__init__ = BaseProcess.__init__
# origin_start = BaseProcess.start
# origin_bootstrap = BaseProcess._bootstrap
# origin_run = BaseProcess.run
#
#
# def sw__init__(this: BaseProcess, group=None, target=None, name=None, args=(), kwargs={}, *,
#                daemon=None):
#     print(config.trace_ignore)
#     if target is not None:
#         if kwargs:
#             kwargs["sw_config"] = config.serialize()
#         else:
#             kwargs = {"sw_config": config.serialize()}
#     print("_init_ %s is running" % os.getpid())
#     origin__init__(this, group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
#
#
# def sw_start(this: BaseProcess):
#     origin_start(this)
#     print("start %s is running" % os.getpid())
#
#
# def sw_run(this: BaseProcess):
#     print("run %s is running" % os.getpid())
#     origin_run(this)
#
#
# def sw_bootstrap(this: BaseProcess, parent_sentinel=None):
#     print("bootstrap %s is running" % os.getpid())
#     origin_bootstrap(this, parent_sentinel=parent_sentinel)
#
#
# def test_decorator():
#     def decorator(func):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             if kwargs is not None and "sw_config" in kwargs:
#                 print(kwargs.pop('sw_config', None))
#                 print(agent.started())
#                 if agent.started() is False:
#                     agent.start()
#             func(*args, **kwargs)
#
#         return wrapper
#
#     return decorator
#
#
# # @test_decorator()
# def test(name):
#     # agent.start()
#     print(name)
#     print("test %s is running" % os.getpid())
#     print(get_context())
#     print(get_context().active_span())
#     requests.post("http://www.baidu.com")
#
#
# def test2(name):
#     # agent.start()
#     print(name)
#     print("test %s is running" % os.getpid())
#     print(get_context())
#     print(get_context().active_span())
#     with get_context().new_local_span("/test") as span:
#         span.tag(Tag(key="huawei", val="test"))
#         requests.post("http://www.baidu.com")
#
#
# # 定义一个要共享实例化对象的类
# class TestClass():
#     def __init__(self):
#         self.test_list = ["start flag"]
#
#     def test_function(self, arg):
#         self.test_list.append(arg)
#
#     def print_test_list(self):
#         for item in self.test_list:
#             print(f"{item}")
#
#
# class SwProcess(Process):
#
#     def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, *,
#                  daemon=None):
#         super(SwProcess, self).__init__(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
#         self._sw_config = config.serialize()
#
#     def run(self):
#         if agent.started() is False:
#             config.deserialize(self._sw_config)
#             agent.start()
#
#         super(SwProcess, self).run()
#
#
# if __name__ == '__main__':
#     # manager = BaseManager()
#     # # 一定要在start前注册，不然就注册无效
#     # manager.register('Test', TestClass)
#     # manager.start()
#     # obj = manager.Test()
#
#     # config.service_name = 'consumer'
#     # config.logging_level = 'DEBUG'
#     # config.trace_ignore = True
#     # agent.start()
#     #
#     # # BaseProcess.__init__ = sw__init__
#     # # BaseProcess.start = sw_start
#     # # BaseProcess._bootstrap = sw_bootstrap
#     # # BaseProcess.run = sw_run
#     #
#     # print("main %s is running" % os.getpid())
#     #
#     # # @runnable
#     #
#     # p1 = SwProcess(target=test, args=('anni',))
#     # p1.start()
#     # p2 = SwProcess(target=test2, args=('anni',))
#     # p2.start()
#     #
#     # time.sleep(50)
#     pass
