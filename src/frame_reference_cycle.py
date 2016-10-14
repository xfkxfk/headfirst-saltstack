import gc
import inspect


def print_frame_cycle_reference():
    frame = inspect.currentframe()
    print 'referrers:', gc.get_referrers(frame.f_locals)
    print 'referents:', gc.get_referents(frame.f_locals)

if __name__ == '__main__':
    print_frame_cycle_reference()
