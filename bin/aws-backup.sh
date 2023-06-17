#!/bin/bash

# This script backs up production data to Amazon S3 using
# the AWS command line interface. Customise to meet your
# own needs.


# Configuration
APP_ROOT=/home/caves/caves.app
BUCKET=s3://caves.app-backup
LOGFILE=$APP_ROOT/data/production/logs/aws/s3-sync.log


aws s3 sync $APP_ROOT/data/production/backups/db $BUCKET/db \
    --exclude "**/postgres-latest.sql.gz" >> $LOGFILE
aws s3 sync $APP_ROOT/data/production/backups/crontab $BUCKET/crontab >> $LOGFILE
aws s3 sync $APP_ROOT/data/production/logs $BUCKET/logs >> $LOGFILE
aws s3 sync $APP_ROOT/bin $BUCKET/bin >> $LOGFILE
aws s3 sync $APP_ROOT/config $BUCKET/config/app >> $LOGFILE
aws s3 sync /etc/nginx/sites-available $BUCKET/config/nginx/sites-available >> $LOGFILE
