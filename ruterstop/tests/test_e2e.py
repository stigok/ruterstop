import os
from subprocess import check_output, PIPE
from os import path
from unittest import TestCase


def run(args):
    cwd = path.dirname(path.realpath(__file__))
    exe = path.join(cwd, "..", "__init__.py")
    out = check_output(["python", exe] + args)
    lines = out.decode("utf8").split('\n')
    return lines

class E2ETestCase(TestCase):
    def test_no_errors(self):
        """
        This is ment to hit natural code paths to detect some runtime errors.
        Might at least catch some bad import statements or missing kwarg defaults.

        NOTE: Will perform a live request.
        """
        lines = run(["--stop-id", "6013", "--direction", "outbound", "--min-eta", "0"])
        lines = list(filter(None, lines)) # remove empty lines
        self.assertGreater(len(lines), 1)
        for line in lines:
            print(line)
