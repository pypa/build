# python-build

A simple, correct PEP517 package builder.

```sh
$ python -m build -h
usage: python -m build [-h] [--verbose] [--sdist] [--wheel] [--outdir ./dist] [.]

positional arguments:
  .                     source directory (defaults to current directory)

optional arguments:
  -h, --help            show this help message and exit
  --verbose, -v         enable verbose output
  --sdist, -s           build a source package
  --wheel, -w           build a wheel
  --outdir ./dist, -o ./dist
                        output directory
  --skip-dependencies, -x
                        does not check for the dependencies
```
