#/!bin/bash

[ $USER = 'root' ] && echo "this script can not be run as root/sudo" && exit 1
echo "Running $0 at `date`"
echo "Performing POST-update/migration tasks..."
UPDATE_PERMISSION_PATHS="media/images/web-snap
media/images/ad-rep
media/dynamic
urls_local
media/feed"
for path in $UPDATE_PERMISSION_PATHS
do
    sudo chown -R :www-data $path
	sudo chmod -R g+w $path
done

find media/coupon-widgets/ -name \*.js -delete

echo -n "Run site.save() loop for all sites? [y/N]:"
read YESNO
[ "$YESNO" = 'y' ] || [ "$YESNO" = 'Y' ] && ../webconfig/scripts/init_10coupons_sites.py
