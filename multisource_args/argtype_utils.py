import argparse

def intlt(bounds):
    start, end = bounds if type(bounds) is tuple else (0, bounds)
    def fntr(x):
        x = int(x)
        if x < start or x >= end: raise argparse.ArgumentTypeError("%d must be in [%d, %d)" % (x, start, end))
        return x
    return fntr

def remap(options):
    key_type = list(set(type(k) for k in options.keys()))[0]
    value_type = list(set(type(k) for k in options.values()))[0]
    def fntr(x):
        try:
            if value_type(x) in options.values(): return value_type(x)
        except: pass
        try:
            if key_type(x) in options.keys(): return options[key_type(x)]
        except: pass

        raise argparse.ArgumentTypeError(f"{str(x)} (type {type(x)}) is not a valid option: {str(options)}")
    return fntr
