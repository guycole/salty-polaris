#!/bin/bash
#
# Title: vessel_collector.sh
# Description: vessel collection
# Development Environment: Debian 10 (buster)/raspian
# Author: Guy Cole (guycole at gmail dot com)
#
# * * * * * /home/gsc/Documents/github/salty-polaris/bin/vessel_collector.sh > /dev/null 2>&1
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#LD_LIBRARY_PATH=/usr/local/lib/arm-linux-gnueabihf; export LD_LIBRARY_PATH
#
echo "start vessel collection"
cd /home/gsc/Documents/github/salty-polaris/src/collection
source venv/bin/activate
python3 ./vessels.py
echo "end vessel collection"
#

