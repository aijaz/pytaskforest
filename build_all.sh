#!/bin/bash

# Remove all containers
docker rm -vf $(docker ps -aq) > /dev/null 2>&1

# Remove all images
#docker rmi -f $(docker images -aq) > /dev/null 2>&1

docker network rm aijaz_network

for f in flask nginx;
  do
    pushd $f || exit 1
    ./build.sh
    popd || exit 1
  done

