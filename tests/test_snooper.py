from decorator_libs import pysnooper_click_able


@pysnooper_click_able.snoop()
def fun2(x):
    x += 1
    x += 2
    print(x)


fun2(0)
