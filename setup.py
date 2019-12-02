from setuptools import setup

setup(
    name="ruterstop",
    description="Et program som viser sanntidsinformasjon for stoppesteder i Oslo og Akershus.",
    version="0.1.0",
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
    ],
    install_requires=[
        "bottle",
        "requests",
    ],
    test_suite="ruterstop.tests",
)
