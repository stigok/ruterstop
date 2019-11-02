#!/bin/bash

set -e

# Change working directory to repo root
src="$(dirname "$(readlink -f "$0")")"
cd "$src/.."

for f in .docker/*.Dockerfile
do
  test_name=$(basename $f | cut -d . -f 1)
  tag=ruterstop-${test_name}

  echo "*** Building ${tag} ***"
  docker build -f ${f} --tag ${tag} . > /dev/null

  echo "*** Running ${tag} ***"
  docker run ${tag}
done
