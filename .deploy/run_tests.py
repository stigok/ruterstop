#!/usr/bin/env python3
from subprocess import run
from sys import argv, exit

PYVER = argv[1]
IMAGE = f"ruterstop:python{PYVER}"

print("Building", IMAGE)
run(
    [
        "docker",
        "build",
        "--network=host",
        "--file=.deploy/Dockerfile",
        f"--build-arg=PYTHON_VERSION={PYVER}",
        f"--build-arg=POETRY_VERSION=1.1.5",
        f"--tag=ruterstop:python{PYVER}",
        ".",
    ],
    check=True,
)

print("Running unit-tests", IMAGE)
run(
    [
        "docker",
        "run",
        "--network=host",
        "--rm",
        IMAGE,
    ]
    + ["unittest"],
    check=True,
)

print("Running livetest", IMAGE)
run(
    [
        "docker",
        "run",
        "--network=host",
        "--rm",
        IMAGE,
    ]
    + ["ruterstop", "--stop-id=6013"],
    check=True,
)

print("Success!")
