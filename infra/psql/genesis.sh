#!/bin/bash
#
# Title:genesis.sh
# Description: database setup
# Development Environment: OS X 12.7.6/postgres 15.8
#
# macbook 
# psql -U gsc template1
createuser -U gsc -d -e -l -P -r -s polaris_admin
woofwoof
createuser -U gsc -e -l -P polaris_client
batabat
#
# linux su - postgres
psql -U postgres template1
createuser -U postgres -d -e -l -P -r -s polaris_admin
woofwoof
createuser -U postgres -e -l -P polaris_client
batabat
#
createdb polaris -O polaris_admin -E UTF8 -T template0 -l C
#
# psql -h localhost -p 5432 -U polaris_admin -d polaris
# psql -h localhost -p 5432 -U polaris_client -d polaris
#