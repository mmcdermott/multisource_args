from multisource_args import *

# Example Args (With associated constants; for reference only)
LOG_STRS = {
    'info': 0,
    'warning': 1,
    'error': 2,
}

@dataclass
class ExampleArgs(BaseArgs):
    output_dir:                  str # Required
    do_bool_arg:                bool = True
    int_arg:                     int = 60000
    float_arg:                 float = 1.0

    # Args for demonstrating helpers
    # Note that right now, the validations aren't really applied at the dataclass level, just in the
    # constructed argparse spec.
    log_level:                   int = 0
    num_layers:                  int = 2

    @classmethod
    def _build_argparse_spec(cls, parser):
        parser.add_argument('--output_dir', type=str)
        cls.add_bool_arg(parser, 'do_bool_arg', help_msg="Bool argument.", default=True)
        parser.add_argument('--int_arg', default=42, type=int, help='int arg')
        parser.add_argument('--float_arg', default=42.42, type=float, help='float arg')

        parser.add_argument('--log_level', default=0, type=remap(LOG_STRS),
                            help="Argument demonstrating the `remap` helper.")
        parser.add_argument('--num_layers', default=1, type=intlt(3),
                            help="Argument demonstrating the `intlt` helper.")

        return 'output_dir', 'filename.json'

# Later (in same file or different, with appropriate imports), do:
if __name__=="__main__":
    args = ExampleArgs.from_commandline()
    # This will inherently encompass both reading from command line and from a config file.
