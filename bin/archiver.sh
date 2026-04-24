#!/bin/bash
#
# Title: archiver.sh
# Description: archive polaris files to tar
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
#
TODAY=$(date '+%Y-%m-%d')
FILE_NAME="polaris-${TODAY}.tgz"
#
EXPORT_DIR="export"
FRESH_DIR="fresh"
SUCCESS_DIR="success"
TO_S3_DIR="to_s3"
WORK_DIR="/var/polaris"
#
echo "start archive"
#
cd ${WORK_DIR}
mv ${FRESH_DIR} ${EXPORT_DIR}
mkdir ${FRESH_DIR}
mv ${SUCCESS_DIR}/* ${EXPORT_DIR}
tar -cvzf ${FILE_NAME} ${EXPORT_DIR}
mv ${FILE_NAME} ${TO_S3_DIR}
#
echo "cleanup"
rm -rf ${EXPORT_DIR}
#
echo "end archive"
#
