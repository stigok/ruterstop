#!/bin/sh
# Build and run a Docker image based on a specific Python version
set -eu

# Change working directory to repo root (if this script's in .docker)
src="$(dirname "$(readlink -f "$0")")"
cd "$src/.."

pyver=$1
shift
test_name=${1}
shift
tag=ruterstop:${test_name}-${pyver}

set -x
docker build --network host \
             --file ${src}/Dockerfile.${test_name} \
             --build-arg PYVER="$pyver" \
             --tag ${tag} \
             . > /dev/null

docker run --network host $tag $@
