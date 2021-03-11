import argparse, dataclasses, json, os, pickle, yaml
from abc import ABC, abstractmethod
from typing import Sequence
from dataclasses import dataclass, asdict
from pathlib import Path, PosixPath

from .argtype_utils import *

JSON, PKL, YAML = 'json', 'pkl', 'yaml'
ARGS = 'args'

class BaseArgs:
    DESCRIPTION = "Base Descriptions (overwrite)"
    DEFAULT_EXTENSION = JSON
    FILENAME = ARGS

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
    def _build_argparse_spec(cls, parser):
        """
        Attempts to automatically infer the argparse spec from the dataclass specification. Largely this is a
        simple mapping of names, type functions, and default values from the dataclases fieldset to the
        argparse API. Two things make this more challenging:
          1. Help messages
          2. The output directory arg
        To accomodate these, the function does the following:
          1. Help messages are by default empty. They can be specified in the dataclass spec using the fields
          interface and the metadata option, setting the key `help_message` to the desired string. See below
          for an example.
          2. If the first argument is a string in the dataclass spec, it is assumed to be the ouptut dir arg.
          This assumption can be overwritten (or confirmed) by using the metadata option and setting the key
          `is_output_dir_arg` to True. See below for an example.

        Metadata interface example:
        ```
        import dataclasses

        @dataclasses.dataclass
        class ExampleArgs(BaseArgs):
            not_output_dir: str # this would normally be flagged as the output dir, but it is overwritten.
            output_dir_metadata: str = dataclasses.field(metadata={'is_output_dir_arg': True})
            has_help_str: int = dataclasses.field(metadata={'help_message': "Insert help string here."})
        ```

        This function can still be overwritten on a class-by-class basis with a custom argparse spec.
        """

        fields = dataclasses.fields(cls)
        output_dir_arg = None
        for i, field in enumerate(fields):
            name, type_fn, default, metadata = field.name, field.type, field.default, field.metadata

            is_bool_arg = type_fn is bool
            is_required = isinstance(default, dataclasses._MISSING_TYPE)
            default_val = None if is_required else default
            help_message = metadata.get('help_message', '')
            is_valid_output_dir_arg = (i == 0 and type_fn is str) or metadata.get('is_output_dir_arg', False)
            if is_valid_output_dir_arg:
                output_dir_arg = name

            if is_bool_arg:
                assert name.startswith('do_'), \
                    f"Default argparse spec requires bool args to start with `do_`. {name} violates."
                cls.add_bool_arg(parser, name, help_message, default_val, required=is_required)
            else:
                parser.add_argument(
                    f"--{name}", type=type_fn, required=is_required, help=help_message, default=default_val
                )

        assert output_dir_arg is not None, "Never found an output dir!"

        return output_dir_arg, cls.FILENAME

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
