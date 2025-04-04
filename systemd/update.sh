cp /home/ubuntu/api/senechal/systemd/* /etc/systemd/system/*
sudo systemctl daemon-reload

sudo systemctl restart senechal_etl_withings.timer
sudo systemctl enable senechal_etl_withings.timer

sudo systemctl restart senechal_etl_garmin.timer
sudo systemctl enable senechal_etl_garmin.timer

sudo systemctl restart senechal_service
