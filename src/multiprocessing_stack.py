import pprint
import inspect
import multiprocessing


def bar():
    stack = inspect.stack()
    pprint.pprint(stack)
    del stack


def foo():
    multiprocessing.Process(target=bar).start()

if __name__ == '__main__':
   foo() 
