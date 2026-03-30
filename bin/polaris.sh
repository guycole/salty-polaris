#!/bin/bash
#
# Title: polaris.sh
# Description: polaris collection cycle
# Development Environment: Debian 10 (buster)/raspian
# Author: Guy Cole (guycole at gmail dot com)
#
# * * * * * /home/gsc/Documents/github/salty-polaris/bin/polaris.sh > /dev/null 2>&1
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#LD_LIBRARY_PATH=/usr/local/lib/arm-linux-gnueabihf; export LD_LIBRARY_PATH
#
echo "start polaris collection"
docker rm polaris
docker run -v /var/polaris:/mnt/polaris --name polaris porlaris:latest
echo "end polaris collection"
#