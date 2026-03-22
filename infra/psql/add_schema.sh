#!/bin/bash
#
# Title:add_schema.sh
# Description:
# Development Environment: OS X 10.15.2/postgres 12.12
# Author: G.S. Cole (guy at shastrax dot com)
#
# psql -U polaris_admin -d polaris
#
export PGDATABASE=polaris
export PGHOST=localhost
export PGPASSWORD=woofwoof
export PGUSER=polaris_admin
#
psql < polaris_load_log.psql
psql < polaris_port.psql
psql < polaris_vessel.psql
#