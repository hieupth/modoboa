#!/bin/sh

# Try running log parser only if the stats plugin is enabled
if python3 /data/instance/manage.py --help | grep -q logparser;
then
	python3 /data/instance/manage.py logparser || exit $?
fi

# “Rotate” the mail log file
echo -n >/var/log/mail.log
kill -1 $(cat /var/run/syslog.pid)