#!/bin/bash

set -e

docker-compose down
./docker-remove-all.sh
#/bin/rm -f example/logs/pytf.log
touch example/logs/pytf.log
./cleanup_example.sh
./build_all.sh
if [ -e example/logs/pytf.log ]; then
    echo log file exists
    cat example/logs/pytf.log
else
  echo log file does not exist
fi
docker-compose up -d
