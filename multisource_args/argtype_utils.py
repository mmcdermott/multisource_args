def intlt(bounds):
    start, end = bounds if type(bounds) is tuple else (0, bounds)
    def fntr(x):
        x = int(x)
        if x < start or x >= end: raise ValueError("%d must be in [%d, %d)" % (x, start, end))
        return x
    return fntr

def remap(options):
    def fntr(x):
        if x in options.values(): return x
        if x in options.keys(): return options[x]
        raise ValueError("%s is not a valid option: %s" % (str(x), str(options)))
    return fntr
