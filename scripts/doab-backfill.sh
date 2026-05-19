#!/bin/bash
# DOAB backfill runner for doab-check (EbookFoundation/doab-check#18).
#
# doab-check runs on a single DigitalOcean droplet under pipenv (NOT Ansible),
# so this is a static, env-configurable script rather than a templated one.
# It mirrors the regluit runner's contract exactly.
#
# One bounded `backfill_doab` pass per cron tick, drained over days, never
# concurrent with the nightly load_doab harvest (shared host flock), halt
# circuit-breaker honored ACROSS ticks via .done/.halted markers.
#
# doab-check's backfill_doab REQUIRES --ids-file (no discovery): supply the
# worklist produced by the doab-check#18 audit via IDS_FILE.
#
# !! CROSS-HOST SLOW-AND-GENTLE INVARIANT !!
# The /var/lock/doab-oai.lock flock is HOST-LOCAL. regluit (AWS) and
# doab-check (DigitalOcean) are separate hosts hitting the SAME DOAB OAI
# endpoint, so the lock does NOT serialise them against each other. Only
# ONE DOAB backfill may be armed at a time across both hosts.
# This runner is INERT until IDS_FILE is set (it hard-refuses below) — that
# opt-in IS the serialisation gate. Before arming this:
#   1. regluit's backfill must be drained (.done present) OR its cron paused
#   2. then set IDS_FILE in this host's crontab to arm doab-check's drain
# Do not run both concurrently; "slow" is the desired posture (Eric).
#
# Exit-code contract (set by the management command):
#   0  drained / nothing-to-do  -> write .done, stop
#   3  benign checkpoint        -> do nothing, cron re-fires
#   4  circuit-breaker halt      -> write .halted, freeze for operator
#   *  unexpected               -> fail safe: write .halted
#
# Suggested crontab (run as the doab-check service user):
#   # nightly harvest must ALSO take the lock — wrap it the same way:
#   30 4 * * *   flock -n /var/lock/doab-oai.lock -c 'cd /path/doab-check && pipenv run python manage.py load_doab "$(date -u -d "3 days ago" +\%Y-\%m-\%d)" >> /var/log/doab-check/doab-harvest.log 2>&1'
#   # minute offset (15,45) vs regluit's 0,30 as defense-in-depth — but the
#   # real guarantee is the cross-host invariant above (only one host armed):
#   15,45 * * * * IDS_FILE=/var/lib/doab-check/backfill/worklist.ids /path/doab-check/scripts/doab-backfill.sh
#
# NOTE: deliberately NOT `set -e` — we must inspect the command's rc.
set -uo pipefail

PROJECT_DIR="${PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
STATE_DIR="${STATE_DIR:-/var/lib/doab-check/backfill}"
LOG="${LOG:-/var/log/doab-check/doab-backfill.log}"
LOCK="${LOCK:-/var/lock/doab-oai.lock}"
IDS_FILE="${IDS_FILE:-}"

DONE="$STATE_DIR/.done"
HALTED="$STATE_DIR/.halted"
STATE="$STATE_DIR/state.json"

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "$(ts) [doab-backfill] $*" >> "$LOG"; }

mkdir -p "$STATE_DIR" "$(dirname "$LOG")" 2>/dev/null || true

if [ -z "$IDS_FILE" ]; then
    log "IDS_FILE not set — doab-check backfill_doab requires --ids-file; refusing to run"
    exit 0
fi
if [ ! -f "$IDS_FILE" ]; then
    log "IDS_FILE $IDS_FILE not found; refusing to run"
    exit 0
fi
if [ -f "$DONE" ]; then
    log ".done present — worklist drained; nothing to do"
    exit 0
fi
if [ -f "$HALTED" ]; then
    log ".halted present — circuit broken; awaiting operator review of $STATE"
    exit 0
fi

exec 9>"$LOCK" || { log "cannot open lock $LOCK; skipping tick"; exit 0; }
if ! flock -n 9; then
    log "DOAB-OAI lock held (harvest or prior backfill running); skipping tick"
    exit 0
fi

log "starting bounded backfill pass (ids-file=$IDS_FILE)"
cd "$PROJECT_DIR" || { log "cd $PROJECT_DIR failed; skipping tick"; exit 0; }

pipenv run python manage.py backfill_doab \
    --ids-file "$IDS_FILE" --state-file "$STATE" >> "$LOG" 2>&1
rc=$?

case "$rc" in
    0)
        touch "$DONE"
        log "DRAINED (rc=0) -> wrote .done; backfill complete"
        ;;
    3)
        log "checkpoint (rc=3) -> cron will re-fire next tick"
        ;;
    4)
        touch "$HALTED"
        log "HALT (rc=4) -> wrote .halted; OPERATOR REVIEW NEEDED ($STATE)"
        ;;
    *)
        touch "$HALTED"
        log "UNEXPECTED rc=$rc -> wrote .halted (fail-safe); OPERATOR REVIEW NEEDED"
        ;;
esac

exit 0
