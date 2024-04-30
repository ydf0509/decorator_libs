"""
超时装饰器
"""
import sys
import threading

# noinspection PyUnusedLocal
import time
import typing
import functools
import time
import signal

class __KThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.killed = False
        self.__run_backup = None

    # noinspection PyAttributeOutsideInit
    def start(self):
        """Start the thread."""
        self.__run_backup = self.run
        self.run = self.__run  # Force the Thread to install our trace.
        threading.Thread.start(self)

    def __run(self):
        """Hacked run function, which installs the trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        return None

    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True


# noinspection PyPep8Naming
class TIMEOUT_EXCEPTION(Exception):
    """function run timeout"""
    pass


def timeout(seconds:int):
    """超时装饰器，指定超时时间

    若被装饰的方法在指定的时间内未返回，则抛出Timeout异常"""

    def timeout_decorator(func):

        def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
            result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))

        def _(*args, **kwargs):
            result = []
            new_kwargs = {
                'oldfunc': func,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }

            thd = __KThread(target=_new_func, args=(), kwargs=new_kwargs)
            thd.start()
            thd.join(seconds)
            alive = thd.isAlive()
            thd.kill()  # kill the child thread

            if alive:
                # raise TIMEOUT_EXCEPTION('function run too long, timeout %d seconds.' % seconds)
                raise TIMEOUT_EXCEPTION(f'{func.__name__}运行时间超过{seconds}秒')
            else:
                if result:
                    return result[0]
                return result

        _.__name__ = func.__name__
        _.__doc__ = func.__doc__
        return _

    return timeout_decorator




def timeout_linux(timeout: int):
    """
    这个不需要单独开一个线程来实现超时,但是只适合linux系统,windwos没有 signal.SIGALRM
    """
    def _timeout_linux(func, ):
        """装饰器，为函数添加超时功能"""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def _timeout_handler(signum, frame):
                """超时处理函数，当接收到信号时抛出异常"""
                raise TimeoutError(f"Function: {func} params: {args}, {kwargs} ,execution timed out: {timeout}")

            # 设置超时信号处理器
            signal.signal(signal.SIGALRM, _timeout_handler)  # 只适合linux 的 timout
            # 启动一个定时器，超时后发送信号
            signal.alarm(timeout)

            try:
                return func(*args, **kwargs)
            finally:
                # 执行完毕记得取消定时器
                signal.alarm(0)  # 关闭定时器

        return wrapper

    return _timeout_linux


if __name__ == '__main__':
    @timeout(3)
    def f(time_to_be_sleep):
        time.sleep(time_to_be_sleep)
        print('hello wprld')

    f(5)
