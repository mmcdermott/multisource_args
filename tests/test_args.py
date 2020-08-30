import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse, contextlib, logging, shlex, shutil, tempfile, unittest
from unittest.mock import patch

from multisource_args.args import *

# Example Args (With associated constants; for reference only)
LOG_STRS = {
    'info': 0,
    'warning': 1,
    'error': 2,
}
OUTPUT_DIR_ARG = 'output_dir'
FILENAME_ARG = 'filename.json'

@dataclass
class ExampleArgs(BaseArgs):
    # Output dir is required
    output_dir:                  str
    do_bool_arg:                bool = True
    int_arg:                     int = 60000
    float_arg:                 float = 1.0

    # Args for demonstrating helpers
    # Note that right now, the validations aren't really applied at the dataclass level, just in the
    # constructed argparse spec.
    log_level:                   int = 0
    num_layers:                  int = 2

    DESCRIPTION = "Example program description."

    @classmethod
    def _build_argparse_spec(cls, parser):
        parser.add_argument(f"--{OUTPUT_DIR_ARG}", type=str, required=True)

        cls.add_bool_arg(parser, 'do_bool_arg', help_msg="Bool argument.", default=True)
        parser.add_argument('--int_arg', default=42, type=int, help='int arg')
        parser.add_argument('--float_arg', default=42.42, type=float, help='float arg')

        parser.add_argument('--log_level', default=0, type=remap(LOG_STRS),
                            help="Argument demonstrating the `remap` helper.")
        parser.add_argument('--num_layers', default=1, type=intlt(3),
                            help="Argument demonstrating the `intlt` helper.")

        return OUTPUT_DIR_ARG, FILENAME_ARG

class TestArgs(unittest.TestCase):
    def setUp(self):
        self.output_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.output_dir)

    def build_default_args(self, default_args = {
        'do_bool_arg': True,
        'int_arg': 5,
        'float_arg': 3.14,
        'log_level': LOG_STRS['info'],
        'num_layers': 2,
    }):
        overall_args = {'output_dir': self.output_dir, **default_args}
        return overall_args, ExampleArgs(**overall_args)

    def test_errors_without_required_args(self):
        with self.assertRaises(Exception):
            args = ExampleArgs()

    def test_construction_as_class(self):
        args_dict, args_cls = self.build_default_args()
        self.assertEqual(vars(args_cls), args_dict)

    def test_file_io(self):
        _, args = self.build_default_args()
        args.to_json_file(os.path.join(self.output_dir, FILENAME_ARG))

        new_args = ExampleArgs.from_json_file(os.path.join(self.output_dir, FILENAME_ARG))

        self.assertEqual(args, new_args)

    def test_reads_from_commandline(self):
        log = logging.getLogger("TestArgs.test_reads_from_commandline")

        cases = [ # [(commandline string, data structure, should error?), ...]
            (
                f"example_main.py --{OUTPUT_DIR_ARG} {self.output_dir} "
                "--no_do_bool_arg --int_arg 3 --float_arg 4.2 --log_level warning --num_layers 2",
                {'do_bool_arg': False, 'int_arg': 3, 'float_arg': 4.2, 'log_level': 1, 'num_layers': 2},
                None
            ), (
                f"example_main.py --{OUTPUT_DIR_ARG} {self.output_dir} "
                "--do_bool_arg --int_arg 2 --float_arg 42.00 --log_level info --num_layers 1",
                {'do_bool_arg': True, 'int_arg': 2, 'float_arg': 42, 'log_level': 0, 'num_layers': 1},
                None
            ), (
                f"example_main.py --{OUTPUT_DIR_ARG} {self.output_dir} "
                "--do_bool_arg --int_arg 2 --float_arg 4.2 --log_level 0 --num_layers 1",
                {'do_bool_arg': True, 'int_arg': 2, 'float_arg': 4.2, 'log_level': 0, 'num_layers': 1},
                None
            ), (
                f"example_main.py --{OUTPUT_DIR_ARG} {self.output_dir} "
                "--do_bool_arg --int_arg 2 --float_arg 4.2 --log_level Information --num_layers 1",
                None,
                SystemExit # should error out as log_level is not in the structure.
            ), (
                f"example_main.py --{OUTPUT_DIR_ARG} {self.output_dir} "
                "--do_bool_arg --int_arg 2 --float_arg 4.2 --log_level info --num_layers 4",
                None,
                SystemExit # Should error out as num_layers is >= 3.
            ), (
                "example_main.py --do_bool_arg --int_arg 2 --float_arg 4.2 --log_level info --num_layers 4",
                None,
                SystemExit # Should error out as it is missing the required argument output_dir.
            ),
        ]

        for cmd_str, want_dict, expected_error in cases:
            new_argv = shlex.split(cmd_str)
            with patch.object(sys, 'argv', new_argv):
                if expected_error is None:
                    args = ExampleArgs.from_commandline(write_args_to_file = False)
                    self.assertEqual(vars(args), {OUTPUT_DIR_ARG: self.output_dir, **want_dict})
                else:
                    with self.assertRaises(expected_error):
                        with open(os.devnull, 'w') as f, contextlib.redirect_stderr(f):
                            args = ExampleArgs.from_commandline(write_args_to_file = False)

    def test_commandline_file_io(self):
        # Writing to file:
        cmd_str = (
            f"sample_main.py --{OUTPUT_DIR_ARG} {self.output_dir} --no_do_bool_arg --int_arg 3 "
            "--float_arg 4.2 --log_level warning --num_layers 2"
        )
        want_dict = {
            OUTPUT_DIR_ARG: self.output_dir, 'do_bool_arg': False, 'int_arg': 3, 'float_arg': 4.2,
            'log_level': 1, 'num_layers': 2
        }
        with patch.object(sys, 'argv', shlex.split(cmd_str)):
            args = ExampleArgs.from_commandline(write_args_to_file = True)

            self.assertTrue(os.path.isfile(os.path.join(self.output_dir, FILENAME_ARG)))

        reloaded_args = ExampleArgs.from_json_file(os.path.join(self.output_dir, FILENAME_ARG))

        self.assertEqual(args, reloaded_args)

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.WARN)
    unittest.main(verbosity=0)
