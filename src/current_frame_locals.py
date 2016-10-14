import inspect


def print_current_frame_locals():
    frame = inspect.currentframe()
    print frame.f_locals

if __name__ == '__main__':
    print_current_frame_locals()
