#!/bin/bash
#

cd /home/ubuntu/doab-check
/home/ubuntu/.local/bin/pipenv run python manage.py dump_checks >> dump_checks.log
gzip dump_checks.csv
mv dump_checks.zip static/dump_checks.zip