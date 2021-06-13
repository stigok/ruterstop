#!/usr/bin/env python3
from subprocess import run, PIPE
from sys import argv

# What command to run in the tests
cmd = argv[1:] or ["--stop-id=6013"]

test_results = dict()

for pyver in ["3.6", "3.7", "3.8"]:
    image = f"ruterstop:python{pyver}"

    print("Building...", image)
    try:
        run(
            [
                "docker",
                "build",
                "--network=host",
                "--file=.deploy/Dockerfile.matrix-unit-tests",
                f"--build-arg=PYTHON_VERSION={pyver}",
                f"--build-arg=POETRY_VERSION=1.1.5",
                f"--tag=ruterstop:python{pyver}",
                ".",
            ],
            text=True,
            check=True,
        )
        test_results[pyver] = "success"
    except CalledProcessError as ex:
        print(ex)
        test_results[pyver] = "failed"

    print("Running", image, cmd)
    run(
        [
            "docker",
            "run",
            "--network=host",
            "--rm",
            image,
        ]
        + cmd
    )

print()
print("Results:")
for pyver, result in test_results.items():
    print("\t", pyver, result)
