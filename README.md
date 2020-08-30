# multisource_args
A simple utility for maintaining arguments that can be used across multiple interfaces (predominately CLI and
Jupyter Notebooks) and making reading and writing arguments to files default. This is based on something I've
used in a few projects and is naturally therefore primarily built with ML research applications in mind, and
arguments will assume that they are instantiated with a "run directory" in mind which is intended to be the
_sole_ directory corresponding to a particular run of the model or instantiation of a dataset/cached dataset.
If such a solution to this problem / similar utility already exists and is better than this, please let me
know (via a github issue).

## Installation
There is no formal distribution on `pip` as of now. But you can install it with `pip`, from github directly,
via `pip install git+https://github.com/mmcdermott/multisource_args`.

## Requirements
  * `>= Python 3.7`

You can use the "conda environment" spec in `env.yml` to meet these requirements, but it solely contains
an appropriate version of python.

## Testing / Examples
Please look at the test code in `tests/` to see examples of this system in use. To run tests, run 
`python -m unittest tests.test_args` (from the main repository directory).
