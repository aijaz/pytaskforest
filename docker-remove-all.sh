#!/bin/sh

# Remove all containers
docker rm -vf $(docker ps -aq) > /dev/null 2>&1
# Remove all images
docker rmi -f $(docker images -aq) > /dev/null 2>&1
# Remove all volumes
docker volume prune -f
