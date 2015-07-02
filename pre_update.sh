#!/bin/bash
[ $USER = 'root' ] && echo "this script can not be run as root/sudo" && exit 1

echo "Running $0 at `date`"
echo "Performing Pre-update/migration tasks..."
source tenrc
echo "Saving Market Data"
python manage.py dumpdata market --indent=4 | sed -e '/ *"coordinate":/d' -e '/ *"envelope":/d' -e '/ *"geom":/d' >market/fixtures/prod_data.json
#svn commit market/fixtures/prod_data.json -m "market data as of `date`"
hg commit market/fixtures/prod_data.json -m "market data as of `date`" 
