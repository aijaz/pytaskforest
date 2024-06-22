#!/bin/bash

if /Users/aijaz/src/Aijaz/pytaskforest/.venv/bin/python /Applications/PyCharm.app/Contents/plugins/python/helpers/pycharm/_jb_pytest_runner.py --path /Users/aijaz/src/Aijaz/pytaskforest/tests
then
    afplay /System/Library/Sounds/Purr.aiff &
else
    afplay /System/Library/Sounds/Sosumi.aiff &
fi



