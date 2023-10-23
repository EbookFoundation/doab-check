#!/bin/bash
#

cd /home/ubuntu/doab-check
/home/ubuntu/.local/bin/pipenv run python manage.py dump_checks >> dump_checks.log
gzip doab_checks.csv
mv doab_checks.csv.gz static/doab_checks.csv.gz