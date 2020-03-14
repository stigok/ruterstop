import os
import sys

from setuptools import setup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from ruterstop import __version__

setup(
    name="ruterstop",
    description="Et program som viser sanntidsinformasjon for stoppesteder i " +
                "Oslo og Akershus.",
    version=__version__,
    url="https://github.com/stigok/ruterstop",
    author="stigok",
    author_email="stig@stigok.com",
    packages=["ruterstop"],
    entry_points={
        "console_scripts": [
            "ruterstop = ruterstop:main",
        ],
    },
    tests_require=[
        "freezegun",
        "webtest",
    ],
    install_requires=[
        "bottle",
        "requests",
    ],
    test_suite="ruterstop.tests",
)
