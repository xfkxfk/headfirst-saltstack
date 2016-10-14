import inspect
import pprint


def bar():
    stack = inspect.stack()
    pprint.pprint(stack)
    del stack


def foo():
    bar()

if __name__ == '__main__':
   foo() 
