#!/bin/bash

# Remove all containers
docker rm -vf $(docker ps -aq) > /dev/null 2>&1

# Remove all images
docker rmi -f $(docker images -aq) > /dev/null 2>&1

#docker network rm aijaz_network

docker build -t pytf_i -f Dockerfile_pytf .
docker build -t worker_i -f Dockerfile_worker .

pushd rabbitmq || exit 1
docker build -t rabbitmq_i .
popd || exit 1

