from setuptools import setup

setup(
    name="ruterstop",
    description="Et program som viser sanntidsinformasjon for stoppesteder i Oslo og Akershus.",
    version="0.0.2",
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
        "coverage",
        "freezegun",
    ],
    install_requires=[
        "bottle",
        "requests",
    ],
    test_suite="ruterstop.tests",
)
