#!/usr/bin/env python3
import re
import sys
from collections import defaultdict
from subprocess import run
import toml


def panic(msg=None, *args):
    if msg:
        print("panic:", msg, *args)
    sys.exit(1)


#
# Get latest tag
#
latest = run(
    ["git", "tag"],
    text=True,
    capture_output=True,
).stdout.splitlines()[-1]

if not latest:
    panic(f"no tags found")

#
# Get all commits since last tag
#
commits = run(
    [
        "git",
        "log",
        f"{latest}..@",
        "--no-merges",
        "--format=format:%s",
    ],
    capture_output=True,
    text=True,
).stdout.splitlines()

if not commits:
    panic(f"no commits since {latest}")

#
# Build a list of all commit types (prefixes)
#
print(f"Commits since {latest}:")
commit_types = set()
for commit in commits:
    print("  -", commit)
    match = re.findall(r"^(\w+):", commit)
    if match:
        commit_types.add(match[0])
    if "BREAKING" in commit:
        commit_types.add("breaking")
print()

#
# Determine next version
#
ma, mi, pa = [int(v) for v in latest[1:].split(".")]
if "feat" in commit_types:
    mi += 1
    pa = 0
else:
    pa += 1

new_ver = f"{ma}.{mi}.{pa}"
print("Next version deemed to be", new_ver)

#
# Verify files
#
pyproject = toml.load("pyproject.toml")
pyproject_ver = pyproject["tool"]["poetry"]["version"]
if new_ver != pyproject_ver:
    panic(f"Version number mismatch in pyproject.toml ({pyproject_ver} != {new_ver})")

with open("./ruterstop/__init__.py") as f:
    initfile_ver = re.findall(r'^__version__ = "(\d+\.\d+\.\d+)"$', f.read(), re.M)[0]
if initfile_ver != new_ver:
    panic(f"Version number mismatch in __init__.py ({initfile_ver} != {new_ver})")

#
# Verify branch
#
branch = run(["git", "branch", "--show-current"], text=True, capture_output=True)
if branch != "master":
    panic("Not on master branch")

#
# Tag with next version
#
if input(f"Tag v{new_ver}? y/N").lower() == "y":
    run(cmd)
cmd = ["git", "tag", "-a", f"v{new_ver}", "-m", f"{new_ver}"]
