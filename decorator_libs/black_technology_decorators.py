"""
这里是黑科技装饰器，有想法的装饰器
"""
import json
import sys
import time
import traceback
import unittest
from functools import wraps

from nb_log import LogManager


def where_is_it_called(func):
    """一个装饰器，被装饰的函数，如果被调用，将记录一条日志,记录函数被什么文件的哪一行代码所调用，非常犀利黑科技的装饰器"""
    if not hasattr(where_is_it_called, 'log'):
        where_is_it_called.log = LogManager('where_is_it_called').get_logger_and_add_handlers()

    # noinspection PyProtectedMember
    @wraps(func)
    def _where_is_it_called(*args, **kwargs):
        # 获取被调用函数名称
        # func_name = sys._getframe().f_code.co_name
        func_name = func.__name__
        # 什么函数调用了此函数
        which_fun_call_this = sys._getframe(1).f_code.co_name  # NOQA

        # 获取被调用函数在被调用时所处代码行数
        line = sys._getframe().f_back.f_lineno

        # 获取被调用函数所在模块文件名
        file_name = sys._getframe(1).f_code.co_filename

        # noinspection PyPep8
        where_is_it_called.log.debug(
            f'文件[{func.__code__.co_filename}]的第[{func.__code__.co_firstlineno}]行即模块 [{func.__module__}] 中的方法 [{func_name}] 正在被文件 [{file_name}] 中的'
            f'方法 [{which_fun_call_this}] 中的第 [{line}] 行处调用，传入的参数为[{args},{kwargs}]')
        try:
            t0 = time.time()
            result = func(*args, **kwargs)
            result_raw = result
            t_spend = round(time.time() - t0, 2)
            if isinstance(result, dict):
                result = json.dumps(result)
            if len(str(result)) > 200:
                result = str(result)[0:200] + '  。。。。。。  '
            where_is_it_called.log.debug('执行函数[{}]消耗的时间是{}秒，返回的结果是 --> '.format(func_name, t_spend) + str(result))
            return result_raw
        except Exception as e:
            where_is_it_called.log.debug('执行函数{}，发生错误'.format(func_name))
            where_is_it_called.log.exception(e)
            raise e

    return _where_is_it_called


# noinspection PyProtectedMember
class TimerContextManager(object):
    """
    用上下文管理器计时，可对代码片段计时
    """
    log = LogManager('TimerContext').get_logger_and_add_handlers()

    def __init__(self, is_print_log=True):
        self._is_print_log = is_print_log
        self.t_spend = None
        self._line = None
        self._file_name = None
        self.time_start = None

    def __enter__(self):
        self._line = sys._getframe().f_back.f_lineno  # 调用此方法的代码的函数
        self._file_name = sys._getframe(1).f_code.co_filename  # 哪个文件调了用此方法
        self.time_start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.t_spend = time.time() - self.time_start
        if self._is_print_log:
            self.log.debug(f'对下面代码片段进行计时:  \n执行"{self._file_name}:{self._line}" 用时 {round(self.t_spend, 2)} 秒')


"""
@contextmanager
def some_generator(<arguments>):
    <setup>
    try:
        yield <value>
    finally:
        <cleanup>
"""


class ExceptionContextManager:
    """
    用上下文管理器捕获异常，可对代码片段进行错误捕捉，比装饰器更细腻
    """

    def __init__(self, logger_name='ExceptionContextManager', verbose=100, donot_raise__exception=True, ):
        """
        :param verbose: 打印错误的深度,对应traceback对象的limit，为正整数
        :param donot_raise__exception:是否不重新抛出错误，为Fasle则抛出，为True则不抛出
        """
        self.logger = LogManager(logger_name).get_logger_and_add_handlers()
        self._verbose = verbose
        self._donot_raise__exception = donot_raise__exception

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # print(exc_val)
        # print(traceback.format_exc())
        exc_str = str(exc_type) + '  :  ' + str(exc_val)
        exc_str_color = '\033[0;30;45m%s\033[0m' % exc_str
        if self._donot_raise__exception:
            if exc_tb is not None:
                self.logger.error('\n'.join(traceback.format_tb(exc_tb)[:self._verbose]) + exc_str_color)
        return self._donot_raise__exception  # __exit__方法必须retuen True才会不重新抛出错误


# noinspection PyMethodMayBeStatic
class _Test(unittest.TestCase):
    # @unittest.skip
    def test_timer_context(self):
        """
        测试上下文，对代码片段进行计时
        """
        with TimerContextManager(is_print_log=True):
            print('测试这里面的代码片段的时间。')
            time.sleep(2)

    @unittest.skip
    def test_where_is_it_called(self):
        """测试函数被调用的装饰器，被调用2次将会记录2次被调用的日志"""

        @where_is_it_called
        def f9(a, b):
            result = a + b
            print(result)
            time.sleep(0.1)
            return result

        f9(1, 2)

        f9(3, 4)

    @unittest.skip
    def test_exception_context_manager(self):
        def f1():
            # noinspection PyStatementEffect,PyTypeChecker
            1 + '2'

        def f2():
            f1()

        def f3():
            f2()

        def f4():
            f3()

        def run():
            f4()

        # noinspection PyUnusedLocal
        with ExceptionContextManager() as ec:
            run()

        print('finish')

    @unittest.skip
    def test_timeout(self):
        """
        测试超时装饰器
        :return:
        """


if __name__ == '__main__':
    unittest.main()
