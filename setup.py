from setuptools import setup

setup(
    name='ruterstop',
    version='0.0.1',
    url="https://github.com/stigok/ruterstop",
    author="stigok",
    author_email="stig@stigok.com",
    packages=["ruterstop"],
    scripts=['bin/ruterstop',],
    tests_require=[
        "coverage",
        "freezegun",
    ],
    install_requires=[
        "bottle",
        "requests",
    ],
    test_suite="ruterstop.tests",
)
