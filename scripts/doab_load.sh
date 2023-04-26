#!/bin/bash
#

cd /home/ubuntu/doab-check
/home/ubuntu/.local/bin/pipenv run python manage.py load_doab >> logs/cron_load.log
