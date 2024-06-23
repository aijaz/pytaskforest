#!/bin/bash

for f in `find example -type d -d 2` ; do echo $f; trash $f; done
