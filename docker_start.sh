#!/bin/bash

if [ -f "conf/cascade.yml" ]; then
   echo "cascade.yml found. Using existing configuration."
else
   echo "cascade.yml not found. Generating new config file from defaults"
   python cascade.py --setup_with_defaults
fi

python cascade.py -vv


