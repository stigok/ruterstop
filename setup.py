import ast
import re

from setuptools import setup


_version_re = re.compile(r"__version__\s+=\s+(.*)")

with open("ruterstop/__init__.py", "rb") as f:
    version = str(
        ast.literal_eval(_version_re.search(f.read().decode("utf-8")).group(1))
    )


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="ruterstop",
    description="Et program som viser sanntidsinformasjon for stoppesteder i Oslo og deler av Viken.",
    version=version,
    long_description=readme(),
    long_description_content_type="text/markdown",
    keywords="entur ruter ruter-api kollektivtransport oslo viken sanntid",
    url="https://github.com/stigok/ruterstop",
    project_urls={
        "Bug Tracker": "http://github.com/stigok/ruterstop/issues",
        "Documentation": "http://github.com/stigok/ruterstop/",
        "Source Code": "http://github.com/stigok/ruterstop/",
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
    ],
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
