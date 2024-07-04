#!/bin/bash

set -e

docker-compose down
./docker-remove-all.sh
touch example/logs/pytf.log
./cleanup_example.sh
./build_all.sh
if [ -e example/logs/pytf.log ]; then
    echo log file exists
else
  echo log file does not exist
fi
docker-compose up -d
