#!/bin/bash

n=1

echoerr() { echo "$@" 1>&2; }

while [[ $n -lt 3 ]]; do
  echo "$n `date`"
  echoerr "****** $n `date`"
  n=$((n+1))
  sleep 0.1
done

echo "DONE"
foobar
baz
echo "DONE2"
