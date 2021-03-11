import argparse, json, os, pickle, yaml
from abc import ABC, abstractmethod
from typing import Sequence
from dataclasses import dataclass, asdict
from pathlib import Path, PosixPath

from .argtype_utils import *

JSON, PKL, YAML = 'json', 'pkl', 'yaml'

class BaseArgs(ABC):
    DESCRIPTION = "Base Descriptions (overwrite)"
    DEFAULT_EXTENSION = JSON

    LOADERS_AND_DUMPERS = {
        # Format:
        # 'extension': (loader, dumper, uses_binary)
        JSON: (json.load, lambda obj, f: json.dump(obj, f, indent=4), False),
        PKL: (pickle.load, pickle.dump, True),
        YAML: (lambda f: yaml.load(f, Loader=yaml.SafeLoader), yaml.dump, False),
    }

    @classmethod
    def _fileio_helper(cls, filepath, filetype=None):
        """
        Reads arguments from file @ filepath. If filetype is None, file type is determined by filepath
        extension.
        """
        assert isinstance(filepath, (str, PosixPath)), \
            f"`filepath` must be a path(able) object! Got type {type(filepath)}: {filepath}"

        if type(filepath) is str: filepath = Path(filepath)

        if filetype is None: filetype = filepath.suffix[1:] # Drop the first character as it is a '.'

        assert filetype in cls.LOADERS_AND_DUMPERS, \
            f"Invalid filetype {filetype}! Must be in {cls.LOADERS_AND_DUMPERS.keys()}"

        loader, dumper, use_binary = cls.LOADERS_AND_DUMPERS[filetype]

        read_mode = 'rb' if use_binary else 'r'
        write_mode = 'wb' if use_binary else 'w'

        def read(cls, filepath):
            with open(filepath, mode=read_mode) as f: contents = loader(f)
            return cls(**contents) if isinstance(contents, dict) else contents

        def write(obj, filepath):
            with open(filepath, mode=write_mode) as f: dumper(obj.to_dict(), f)

        return filepath, read, write

    @classmethod
    def from_file(cls, filepath, filetype=None):
        filepath, reader, _ = cls._fileio_helper(filepath, filetype)

        assert filepath.is_file(), f"`filepath` ({filepath}) must be a file!"
        return reader(cls, filepath)

    def to_file(self, filepath, filetype=None):
        filepath, _, writer = self._fileio_helper(filepath, filetype)

        if filepath.exists():
            assert filepath.is_file(), f"Can't write args to {filepath}: path exists and is a non-file!"
            print(f"Overwriting existing args at {filepath}")

        writer(self, filepath)

    def to_dict(self): return asdict(self)

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
        parser = argparse.ArgumentParser(description=cls.DESCRIPTION)

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
        args_dict = vars(args)

        args_dir = Path(args_dict[main_dir_arg])
        args_filepath = args_dir / args_filename
        if not args_filepath.suffix: args_filepath = args_filepath.with_suffix(f".{cls.DEFAULT_EXTENSION}")

        if args.do_load_from_dir:
            new_args = cls.from_file(args_filepath)
            assert vars(new_args)[main_dir_arg] == args_dir, f"{main_dir_arg} doesn't match loaded file!"

            return new_args

        if 'do_load_from_dir' in args_dict: args_dict.pop('do_load_from_dir')
        args_cls = cls(**args_dict)

        if write_args_to_file:
            if not args_dir.is_dir():
                assert not args_dir.exists(), f"{args_dir} exists and is non-directory! Can't save within."
                print(f"Making save dir: {args_dir}")
                os.makedirs(args_dir)

            args_cls.to_file(args_filepath)

        return args_cls
