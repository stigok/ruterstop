#!/bin/bash

set -eu

# Change working directory to repository root,
# expecting this script to reside at :/.docker/<script>
src="$(dirname "$(readlink -f "$0")")"
cd "$src/.."

dockerfile="$src/Dockerfile"

proxy_serv="http://127.0.0.1:8080"
proxy_args="--build-arg http_proxy=$proxy_serv --build-arg https_proxy=$proxy_serv"

for pyver in 3.5 3.6 3.7 3.8
do
  echo $pyver
  tag=ruterstop-python${pyver}

  echo "*** Building ${tag} ***"
  docker build -f ${dockerfile} \
         --build-arg PYVER=$pyver \
         $proxy_args \
         --network host \
         --tag ${tag} \
         . > /dev/null

  echo "*** Running ${tag} ***"
  runcmd="docker run \
         --network host \
         --volume $HOME/.mitmproxy/mitmproxy-ca-cert.cer:/usr/local/share/ca-certificates/mitmproxy.crt \
         --env http_proxy=$proxy_serv \
         --env https_proxy=$proxy_serv \
         --env HTTP_PROXY=$proxy_serv \
         --env HTTPS_PROXY=$proxy_serv \
         --env REQUESTS_CA_BUNDLE=/usr/local/share/ca-certificates/mitmproxy.crt \
         $tag"

  $runcmd sh -c "update-ca-certificates > /dev/null \
              && python setup.py test > /dev/null"
  $runcmd sh -c "update-ca-certificates > /dev/null \
              && ruterstop --stop-id 6013 --direction outbound --min-eta 2"
done
