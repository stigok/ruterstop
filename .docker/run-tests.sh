#!/bin/bash

set -eu

# Change working directory to repository root,
# expecting this script to reside at :/.docker/<script>
src="$(dirname "$(readlink -f "$0")")"
cd "$src/.."

dockerfile="$src/Dockerfile"

function run() {
  pyver=$1
  echo $pyver
  tag=ruterstop:python${pyver}

  echo "*** Building ${tag} ***"
  docker build -f ${dockerfile} \
         --build-arg PYVER=$pyver \
         --tag ${tag} \
         .

  echo "*** Running ${tag} ***"
  runcmd="docker run $tag"

  $runcmd sh -c "python setup.py test"
  $runcmd sh -c "ruterstop --stop-id 6013 --direction outbound --min-eta 2"
}


if [ -n ${1:-''} ]
then
  run $1
else
  for pyver in 3.5 3.6 3.7 3.8
  do
    run $pyver
  done
fi
