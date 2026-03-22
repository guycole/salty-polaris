#!/bin/bash
#
# Title:drop_schema.sh
# Description: remove schema
# Development Environment: OS X 10.15.2/postgres 12.12
# Author: G.S. Cole (guy at shastrax dot com)
#
export PGDATABASE=polaris
export PGHOST=localhost
export PGPASSWORD=woofwoof
export PGUSER=polaris_admin
#
psql $PGDATABASE -c "drop table polaris_port"
psql $PGDATABASE -c "drop table polaris_vessel"
psql $PGDATABASE -c "drop table polaris_load_log"
#
