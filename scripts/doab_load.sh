#!/bin/bash
#
# Nightly DOAB OAI harvest.
#
# Passing an explicit `from_date` (3 days back, rolling window) routes
# through the if-from_date branch in load_doab_oai. The no-from_date path
# stalls on pyoai's resumption-token follow-up and freezes the cursor —
# see EbookFoundation/doab-check#12. load_doab dedupes by record id, so
# the 3-day overlap is cheap and resilient to occasional missed nights.
#
# Captures stderr too so sentinel-write failures from the Retry-After
# logic (#14) are visible in the cron log, not lost to root mail.

cd /home/ubuntu/doab-check || exit 1
/home/ubuntu/.local/bin/pipenv run python manage.py load_doab \
    "$(date -u -d '3 days ago' +%Y-%m-%d)" --max=20000 \
    >> logs/cron_load.log 2>&1
