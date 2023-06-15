#!/bin/bash

# Rotate logs in production.

LOG_DIR=/home/andrew/apps/caves.app/data/production/logs

/usr/sbin/logrotate $LOG_DIR/logrotate.conf -s $LOG_DIR/logrotate.status
