# coding=utf-8
"""
这里面是常规的装饰器，实现简单
"""

import base64
import copy
import random
import warnings
from multiprocessing import Process

from contextlib import contextmanager
import functools
import json
import os
import sys
import threading
import time
import traceback
import unittest
from functools import wraps
from flask import request as flask_request

from nb_log import LogManager, nb_print

os_name = os.name
handle_exception_log = LogManager('function_error').get_logger_and_add_handlers()
run_times_log = LogManager('run_many_times').get_logger_and_add_handlers(20)


class CustomException(Exception):
    def __init__(self, err=''):
        err0 = 'fatal exception\n'
        Exception.__init__(self, err0 + err)


def run_many_times(times=1):
    """把函数运行times次的装饰器
    :param times:运行次数
    没有捕获错误，出错误就中断运行，可以配合handle_exception装饰器不管是否错误都运行n次。
    """

    def _run_many_times(func):
        @wraps(func)
        def __run_many_times(*args, **kwargs):
            for i in range(times):
                run_times_log.debug('* ' * 50 + '当前是第 {} 次运行[ {} ]函数'.format(i + 1, func.__name__))
                func(*args, **kwargs)

        return __run_many_times

    return _run_many_times


# noinspection PyIncorrectDocstring
def handle_exception(retry_times=0, error_detail_level=0, is_throw_error=False, time_sleep=0):
    """捕获函数错误的装饰器,重试并打印日志
    :param retry_times : 重试次数
    :param error_detail_level :为0打印exception提示，为1打印3层深度的错误堆栈，为2打印所有深度层次的错误堆栈
    :param is_throw_error : 在达到最大次数时候是否重新抛出错误
    :type error_detail_level: int
    """

    if error_detail_level not in [0, 1, 2]:
        raise Exception('error_detail_level参数必须设置为0 、1 、2')

    def _handle_exception(func):
        @wraps(func)
        def __handle_exception(*args, **keyargs):
            for i in range(0, retry_times + 1):
                try:
                    result = func(*args, **keyargs)
                    if i:
                        handle_exception_log.debug(
                            u'%s\n调用成功，调用方法--> [  %s  ] 第  %s  次重试成功' % ('# ' * 40, func.__name__, i))
                    return result

                except Exception as e:
                    error_info = ''
                    if error_detail_level == 0:
                        error_info = '错误类型是：' + str(e.__class__) + '  ' + str(e)
                    elif error_detail_level == 1:
                        error_info = '错误类型是：' + str(e.__class__) + '  ' + traceback.format_exc(limit=3)
                    elif error_detail_level == 2:
                        error_info = '错误类型是：' + str(e.__class__) + '  ' + traceback.format_exc()

                    handle_exception_log.error(
                        u'%s\n记录错误日志，调用方法--> [  %s  ] 第  %s  次错误重试， %s\n' % ('- ' * 40, func.__name__, i, error_info))
                    if i == retry_times and is_throw_error:  # 达到最大错误次数后，重新抛出错误
                        raise e
                time.sleep(time_sleep)

        return __handle_exception

    return _handle_exception


def keep_circulating(time_sleep=0.001, exit_if_function_run_sucsess=False, is_display_detail_exception=True, block=True,
                     daemon=False):
    """间隔一段时间，一直循环运行某个方法的装饰器
    :param time_sleep :循环的间隔时间
    :param exit_if_function_run_sucsess :如果成功了就退出循环
    :param is_display_detail_exception
    :param block :是否阻塞主主线程，False时候开启一个新的线程运行while 1。
    :param daemon: 如果使用线程，那么是否使用守护线程，使这个while 1有机会自动结束。
    """
    if not hasattr(keep_circulating, 'keep_circulating_log'):
        keep_circulating.log = LogManager('keep_circulating').get_logger_and_add_handlers()

    def _keep_circulating(func):
        @wraps(func)
        def __keep_circulating(*args, **kwargs):

            # noinspection PyBroadException
            def ___keep_circulating():
                while 1:
                    try:
                        result = func(*args, **kwargs)
                        if exit_if_function_run_sucsess:
                            return result
                    except Exception as e:
                        msg = func.__name__ + '   运行出错\n ' + traceback.format_exc(
                            limit=10) if is_display_detail_exception else str(e)
                        keep_circulating.log.error(msg)
                    finally:
                        time.sleep(time_sleep)

            if block:
                return ___keep_circulating()
            else:
                threading.Thread(target=___keep_circulating, daemon=daemon).start()

        return __keep_circulating

    return _keep_circulating


def synchronized(func):
    """线程锁装饰器，可以加在单例模式上"""
    func.__lock__ = threading.Lock()

    @wraps(func)
    def lock_func(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)

    return lock_func


def singleton(cls):
    """
    单例模式装饰器,新加入线程锁，更牢固的单例模式，主要解决多线程如100线程同时实例化情况下可能会出现三例四例的情况,实测。
    """
    _instance = {}
    singleton.__lock = threading.Lock()

    @wraps(cls)
    def _singleton(*args, **kwargs):
        with singleton.__lock:
            if cls not in _instance:
                _instance[cls] = cls(*args, **kwargs)
            return _instance[cls]

    return _singleton


def flyweight(cls):
    _instance = {}

    def _make_arguments_to_key(args, kwds):
        key = args
        if kwds:
            sorted_items = sorted(kwds.items())
            for item in sorted_items:
                key += item
        return key

    @synchronized
    @wraps(cls)
    def _flyweight(*args, **kwargs):
        cache_key = f'{cls}_{_make_arguments_to_key(args, kwargs)}'
        # nb_print(cache_key)
        if cache_key not in _instance:
            _instance[cache_key] = cls(*args, **kwargs)
        return _instance[cache_key]

    return _flyweight


def timer(func):
    """计时器装饰器，只能用来计算函数运行时间"""
    if not hasattr(timer, 'log'):
        timer.log = LogManager(f'timer_{func.__name__}').get_logger_and_add_handlers(
            log_filename=f'timer_{func.__name__}.log')

    @wraps(func)
    def _timer(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        t_spend = round(t2 - t1, 2)
        timer.log.debug('执行[ {} ]方法用时 {} 秒'.format(func.__name__, t_spend))
        return result

    return _timer


# noinspection PyPep8Naming
class cached_class_property(object):
    """类属性缓存装饰器"""

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = self.func(obj)
        setattr(cls, self.func.__name__, value)
        return value


# noinspection PyPep8Naming
class cached_property(object):
    """实例属性缓存装饰器"""

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        print(obj, cls)
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def cached_method_result(fun):
    """方法的结果装饰器,不接受self以外的多余参数，主要用于那些属性的property方法属性上，这是同时缓存给类和实例。
    配合property装饰器，主要是在pycahrm自动补全上比上面的cached_property装饰器好"""

    @wraps(fun)
    def inner(self):
        if not hasattr(fun, 'result'):
            result = fun(self)
            fun.result = result
            fun_name = fun.__name__
            setattr(self.__class__, fun_name, result)
            setattr(self, fun_name, result)
            return result
        else:
            return fun.result

    return inner


def cached_method_result_for_instance(fun):
    """方法的结果装饰器,不接受self以外的多余参数，主要用于那些属性的property方法属性上,只缓存给实例不缓存到类属性"""

    @wraps(fun)
    def inner(self):
        if not hasattr(fun, 'result'):
            result = fun(self)
            fun.result = result
            fun_name = fun.__name__
            setattr(self, fun_name, result)
            return result
        else:
            return fun.result

    return inner


class FunctionResultCacher:
    logger = LogManager('FunctionResultChche').get_logger_and_add_handlers()
    func_result_dict = {}
    """
    {
        (f1,(1,2,3,4)):(10,1532066199.739),
        (f2,(5,6,7,8)):(26,1532066211.645),
    }
    """

    @classmethod
    def cached_function_result_for_a_time(cls, cache_time: float):
        """
        函数的结果缓存一段时间装饰器,不要装饰在返回结果是超大字符串或者其他占用大内存的数据结构上的函数上面。
        :param cache_time :缓存的时间
        :type cache_time : float
        """

        def _cached_function_result_for_a_time(fun):

            @wraps(fun)
            def __cached_function_result_for_a_time(*args, **kwargs):
                # print(cls.func_result_dict)
                # if len(cls.func_result_dict) > 1024:
                if sys.getsizeof(cls.func_result_dict) > 100 * 1000 * 1000:
                    cls.func_result_dict.clear()

                key = cls._make_arguments_to_key(args, kwargs)
                if (fun, key) in cls.func_result_dict and time.time() - cls.func_result_dict[(fun, key)][
                    1] < cache_time:
                    return cls.func_result_dict[(fun, key)][0]
                else:
                    if (fun, key) in cls.func_result_dict and time.time() - cls.func_result_dict[(fun, key)][
                        1] < cache_time:
                        return cls.func_result_dict[(fun, key)][0]
                    else:
                        cls.logger.debug('函数 [{}] 此次不能使用缓存'.format(fun.__name__))
                        result = fun(*args, **kwargs)
                        cls.func_result_dict[(fun, key)] = (result, time.time())
                        return result

            return __cached_function_result_for_a_time

        return _cached_function_result_for_a_time

    @staticmethod
    def _make_arguments_to_key(args, kwds):
        key = args
        if kwds:
            sorted_items = sorted(kwds.items())
            for item in sorted_items:
                key += item
        return key  # 元祖可以相加。


def deprecated(fn):
    """Mark a function as deprecated and warn the user on use."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        warnings.warn(fn.__doc__.split('\n')[0],
                      category=DeprecationWarning, stacklevel=2)
        return fn(*args, **kwargs)

    return wrapper


def run_in_new_thread(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        threading.Thread(target=f, args=args, kwargs=kwargs).start()

    return wrapper


def run_in_new_process_only_for_linux(f):
    """
    这个只能在linux上使用。linux使用fork，winwows会报错。请使用下一个非装饰器版本。
    :param f:
    :return:
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        Process(target=f, args=args, kwargs=kwargs).start()

    return wrapper


def run_with_specify_process(proccess_num, f, *args, **kwargs):
    [Process(target=f, args=args, kwargs=kwargs).start() for _ in range(proccess_num)]


def add_cors_according_is_mtfy_app_gw(response):
    # deviceid,sn,ts,wechatid,x-access-token
    # if 'mtfy-app-gw'  not in flask_request.headers.get('X-Forwarded-Host',None):
    """
        response['Access-Control-Allow-Origin'] = '*'        #允许的跨域名
                                response['Access-Control-Allow-Headers'] = 'h1'

    """
    if 'mtfy-app-gw' in flask_request.headers.get('X-Forwarded-Host', ''):
        pass
    else:
        response.headers['Access-Control-Allow-Origin'] = flask_request.headers.get('Origin', '*')  #
        response.headers['Allow'] = 'GET, HEAD, POST, OPTIONS, PUT, PATCH, DELETE'
        # 这里的Access-Control-Allow-Headers使用*会造成老的手机系统不支持通配符。同时option请求才有这个键 Access-Control-Request-Headers，所以用headers.get。
        response.headers['Access-Control-Allow-Headers'] = flask_request.headers.get('Access-Control-Request-Headers',
                                                                                     '*')
    return response


# noinspection PyMethodMayBeStatic
class _Test(unittest.TestCase):
    @unittest.skip
    def test_superposition(self):
        """测试多次运行和异常重试,测试装饰器叠加"""

        @run_many_times(3)
        @handle_exception(2, 1)
        def f():
            import json
            json.loads('a', ac='ds')

        f()

    @unittest.skip
    def test_handle_exception(self):
        """测试异常重试装饰器"""
        import requests

        @handle_exception(2)
        def f3():
            pass
            requests.get('dsdsdsd')

        f3()

    @unittest.skip
    def test_run_many_times(self):
        """测试运行5次"""

        @run_many_times(5)
        def f1():
            print('hello')
            time.sleep(1)

        f1()

    @unittest.skip
    def test_singleton(self):
        """测试单例模式的装饰器"""

        @singleton
        class A(object):
            def __init__(self, x):
                self.x = x

        a1 = A(3)
        a2 = A(4)
        self.assertEqual(id(a1), id(a2))
        print(a1.x, a2.x)

    @unittest.skip
    def test_flyweight(self):
        @flyweight
        class A:
            def __init__(self, x, y, z, q=4):
                in_param = copy.deepcopy(locals())
                nb_print(f'执行初始化啦, {in_param}')

        @flyweight
        class B:
            def __init__(self, x, y, z):
                in_param = copy.deepcopy(locals())
                nb_print(f'执行初始化啦, {in_param}')

        A(1, 2, 3)
        A(1, 2, 3)
        A(1, 2, 4)
        B(1, 2, 3)

    # @unittest.skip
    def test_keep_circulating(self):
        """测试间隔时间，循环运行"""

        @keep_circulating(3, block=False)
        def f6():
            print("每隔3秒，一直打印   " + time.strftime('%H:%M:%S'))

        f6()
        print('test block')

    @unittest.skip
    def test_timer(self):
        """测试计时器装饰器"""

        @timer
        def f7():
            time.sleep(2)

        f7()

    # noinspection PyArgumentEqualDefault
    @unittest.skip
    def test_cached_function_result(self):
        @FunctionResultCacher.cached_function_result_for_a_time(3)
        def f10(a, b, c=3, d=4):
            print('计算中。。。')
            return a + b + c + d

        print(f10(1, 2, 3, d=6))
        print(f10(1, 2, 3, d=4))
        print(f10(1, 2, 3, 4))
        print(f10(1, 2, 3, 4))
        time.sleep(4)
        print(f10(1, 2, 3, 4))


if __name__ == '__main__':
    unittest.main()
