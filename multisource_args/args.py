import argparse, json, os, pickle
from abc import ABC, abstractmethod
from typing import Sequence
from dataclasses import dataclass, asdict

from .argtype_utils import *

class BaseArgs(ABC):
    # This could also be extended to support other filetypes (XML, YAML, etc.)
    # If so extended, interface should be DRYed, with a generic "to_file" and "from_file" method taking
    # an optional (filetype) arg that can also be set at a class level (possibly statically), and a
    # dictionary of filetypes to readers/writers.
    @classmethod
    def from_json_file(cls, filepath):
        with open(filepath, mode='r') as f: return cls(**json.loads(f.read()))
    @staticmethod
    def from_pickle_file(filepath):
        with open(filepath, mode='rb') as f: return pickle.load(f)

    def to_dict(self): return asdict(self)
    def to_json_file(self, filepath):
        with open(filepath, mode='w') as f: f.write(json.dumps(asdict(self), indent=4))
    def to_pickle_file(self, filepath):
        with open(filepath, mode='wb') as f: pickle.dump(self, f)

    @classmethod
    @abstractmethod
    def _build_argparse_spec(cls, parser):
        raise NotImplementedError("Must overwrite in base class!")

    @staticmethod
    def add_bool_arg(parser, arg, help_msg, default, required=False):
        """
        Adds a copy of `arg` and `no_{arg}` to the parser.
        """
        assert arg.startswith("do_"), "Arg should be of the form do_*! Got %s" % arg
        do_arg, no_do_arg = "--%s" % arg, "--no_%s" % arg
        parser.add_argument(
            do_arg, action='store_true', dest=arg, help=help_msg, default=default, required=required
        )
        parser.add_argument(no_do_arg, action='store_false', dest=arg)

    @classmethod
    def from_commandline(cls, write_args_to_file=True):
        parser = argparse.ArgumentParser()

        main_dir_arg, args_filename = cls._build_argparse_spec(parser)

        # To load from a run_directory (not synced to overall structure above):
        parser.add_argument(
            "--do_load_from_dir", action='store_true',
            help=f"Should the system reload from the sentinel args.json file in the specified run directory "
                 "(`--{main_dir_arg}`) and use those args rather than consider those set here? If so, no "
                 "other args (beyond {main_dir_arg}) need be set (they will all be ignored).",
            default=False
        )

        args = parser.parse_args()

        if args.do_load_from_dir:
            load_dir = vars(args)[main_dir_arg]
            assert os.path.exists(load_dir), f"{load_dir} must exist!"
            args_path = os.path.join(load_dir, args_filename)
            assert os.path.exists(args_path), f"Args file {args_path} must exist!"

            new_args = cls.from_json_file(args_path)
            assert vars(new_args)[main_dir_arg] == load_dir, f"{main_dir_arg} doesn't match loaded file!"

            return new_args

        args_dict = vars(args)
        if 'do_load_from_dir' in args_dict: args_dict.pop('do_load_from_dir')
        args_cls = cls(**args_dict)

        if write_args_to_file:
            save_dir = vars(args)[main_dir_arg]
            args_path = os.path.join(save_dir, args_filename)
            if os.path.exists(save_dir):
                assert not os.path.exists(args_path), f"{args_path} already exists!"
            else:
                print(f"Making save dir: {save_dir}")
                os.makedirs(save_dir)

            args_cls.to_json_file(args_path)

        return args_cls
