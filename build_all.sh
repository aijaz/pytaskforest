#!/bin/bash

# Remove all containers
docker rm -vf $(docker ps -aq) > /dev/null 2>&1

# Remove all images
docker rmi -f $(docker images -aq) > /dev/null 2>&1

docker network rm aijaz_network

docker build -t pytf_i -f Dockerfile_pytf .
