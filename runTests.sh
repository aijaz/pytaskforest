#!/bin/bash

if pytest -q
then
    afplay /System/Library/Sounds/Purr.aiff &
else
    afplay /System/Library/Sounds/Sosumi.aiff &
fi



