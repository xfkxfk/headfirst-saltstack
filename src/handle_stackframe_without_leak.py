import inspect


def handle_stackframe_without_leak():
    frame = inspect.currentframe()
    try:
        pass # do something with the frame
    finally:
        del frame
