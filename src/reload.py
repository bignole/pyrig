import inspect
import os
import sys


def reload_modules(*args):
    """Reload this package.

    This will delete module if args are in sys.modules.
    """
    for x in sorted(sys.modules):
        if any([True for t in args if t in x]):
            del sys.modules[x]


if __name__ == "__main__":
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    path = os.path.dirname(os.path.abspath(filename))
    modules = [
        name
        for name in os.listdir(path)
        if os.path.isdir(os.path.join(path, name)) and "." not in name
    ]
    reload_modules(*modules)