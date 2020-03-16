import ast
import re

from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('ruterstop/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name="ruterstop",
    description="Et program som viser sanntidsinformasjon for stoppesteder i " +
                "Oslo og Akershus.",
    version=version,
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
