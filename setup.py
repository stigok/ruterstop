from setuptools import setup

setup(
    name='ruterstop',
    version='0.0.1',
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
    test_suite="ruterstop.tests"
)
