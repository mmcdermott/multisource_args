import json, pickle, yaml

from yaml import load, dump
try:
        from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
        from yaml import Loader, Dumper

# TODO(mmd): Finish.
def reader_writer_fntr(ext, loader, dumper, use_binary=False, re_init_class=True):
    read_mode = 'rb' if use_binary else 'r'
    write_mode = 'wb' if use_binary else 'w'

    def read(cls, filepath):
        with open(f"{filepath}.{ext}", mode=read_mode) as f: contents = loader(f)
        return cls(**contents) if re_init_class else contents

    def write(filepath, obj):
        with open(f"{filepath}.{ext}", mode=write_mode) as f: f.write(dumper(obj.to_dict()))
