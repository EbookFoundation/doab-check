#!/bin/bash
#

cd /home/ubuntu/doab-check
/home/ubuntu/.local/bin/pipenv run python manage.py check_items >> cron_check.log
