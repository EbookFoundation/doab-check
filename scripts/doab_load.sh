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
#
# flock /var/lock/doab-oai.lock: same-host serialization with the
# backfill runner (scripts/doab-backfill.sh). At most one DOAB-OAI
# client per host; a tick that finds the lock held simply skips (the
# 3-day rolling window self-heals on the next clear night). Cross-host
# coordination with regluit is the operator-managed CROSS-HOST INVARIANT
# documented in scripts/doab-backfill.sh.
# Retry-After is independently enforced by load_doab.handle() itself.

LOG=/home/ubuntu/doab-check/logs/cron_load.log
LOCK=/var/lock/doab-oai.lock
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }

exec 9>"$LOCK" || { echo "$(ts) [doab_load] cannot open lock $LOCK" >> "$LOG"; exit 0; }
if ! flock -n 9; then
    echo "$(ts) [doab_load] DOAB-OAI lock held (backfill running); skipping this run" >> "$LOG"
    exit 0
fi

cd /home/ubuntu/doab-check || exit 1
/home/ubuntu/.local/bin/pipenv run python manage.py load_doab \
    "$(date -u -d '3 days ago' +%Y-%m-%d)" --max=20000 \
    >> "$LOG" 2>&1
