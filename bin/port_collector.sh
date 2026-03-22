#!/bin/bash
#
# Title: port_collector.sh
# Description: port collection
# Development Environment: Debian 10 (buster)/raspian
# Author: Guy Cole (guycole at gmail dot com)
#
# * * * * * /home/gsc/Documents/github/salty-polaris/bin/port_collector.sh > /dev/null 2>&1
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#LD_LIBRARY_PATH=/usr/local/lib/arm-linux-gnueabihf; export LD_LIBRARY_PATH
#
echo "start port collection"
cd /home/gsc/Documents/github/salty-polaris/src/collection
source venv/bin/activate
python3 ./ports.py
echo "end port collection"
#