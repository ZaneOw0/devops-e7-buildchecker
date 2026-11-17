#!/usr/bin/env bash
# E12 cross-machine API client (241880106, A05).
# Runs on a machine other than the API server and reaches it only through
#   ssh -N -L 18081:127.0.0.1:8081 <account>@<api-server>
# Needs: bash, curl, jq, shasum (or sha256sum).
# usage: e12_xmachine_client.sh REQUEST_JSON OUT_DIR [BASE_URL] [IDEMPOTENCY_KEY]
set -euo pipefail
REQ=$1; OUT=$2; BASE=${3:-http://127.0.0.1:18081}; KEY=${4:-a05-241880106-e12-real-xmachine-01}
WANT=(candidate.patch repair-plan.json validation/validation.json recheck.json)
[ -e "$OUT" ] && { echo "OUTPUT_EXISTS: $OUT" >&2; exit 2; }
mkdir -p "$OUT/http" "$OUT/files"
sha() { if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1; }
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
LOG="$OUT/http-log.tsv"; printf 'time\tmethod\tpath\tstatus\tx_content_sha256\n' > "$LOG"
n=0
# call METHOD PATH [BODY_FILE] -> sets CODE, BODY (file), HDR (file)
call() {
  n=$((n+1)); BODY="$OUT/http/$(printf %02d $n).body"; HDR="$OUT/http/$(printf %02d $n).headers"
  local args=(-sS -o "$BODY" -D "$HDR" -w '%{http_code}' -X "$1")
  [ $# -ge 3 ] && args+=(-H 'Content-Type: application/json' --data-binary "@$3")
  CODE=$(curl "${args[@]}" "$BASE$2")
  local x; x=$(tr -d '\r' < "$HDR" | awk -F': ' 'tolower($1)=="x-content-sha256"{print $2}')
  printf '%s\t%s\t%s\t%s\t%s\n' "$(ts)" "$1" "$2" "$CODE" "$x" >> "$LOG"
}

started=$(ts)
INPUT_SHA=$(jq -cS . "$REQ" | tr -d '\n' | shasum -a 256 | cut -d' ' -f1)
jq -n --arg k "$KEY" --slurpfile i "$REQ" '{idempotency_key:$k,input:$i[0]}' > "$OUT/submit.json"
jq -n --arg k "$KEY" --slurpfile i "$REQ" '{idempotency_key:$k,input:($i[0]|.target=.base)}' > "$OUT/conflict.json"

call GET /health;                         HEALTH="$CODE $(jq -c . "$BODY")"
call POST /v1/jobs "$OUT/submit.json";    SUBMIT_CODE=$CODE; JOB=$(jq -r .job_id "$BODY"); SUBMIT_STATUS=$(jq -r .status "$BODY")
# contract 1: same key + same input -> same job_id, no second build
call POST /v1/jobs "$OUT/submit.json";    DUP_CODE=$CODE; DUP_SAME=$([ "$(jq -r .job_id "$BODY")" = "$JOB" ] && echo true || echo false)
# contract 2: same key + changed target -> 409 IDEMPOTENCY_CONFLICT
call POST /v1/jobs "$OUT/conflict.json";  CONF_CODE=$CODE; CONF_ERR=$(jq -r .error "$BODY")
# manifest is not served before the result exists
call GET "/v1/jobs/$JOB/artifacts";       EARLY_CODE=$CODE; EARLY_ERR=$(jq -r '.error // "already-done"' "$BODY")

deadline=$(( $(date +%s) + 3600 ))
while :; do
  call GET "/v1/jobs/$JOB"; STATUS=$(jq -r .status "$BODY")
  case $STATUS in SUCCEEDED|FAILED|TIMED_OUT) break;; esac
  [ "$(date +%s)" -gt "$deadline" ] && break
  sleep 15
done
cp "$BODY" "$OUT/final-state.json"; TRACE=$(jq -r '.trace_id // ""' "$BODY")

call GET "/v1/jobs/$JOB/artifacts"; cp "$BODY" "$OUT/result.json"
# every artifact://<job>/<relpath> reference with its sha256, as "relpath sha"
jq -r '.. | objects | select((.uri? | type)=="string" and (.uri|startswith("artifact://")) and .sha256?) | "\(.uri|split("/")[3:]|join("/")) \(.sha256)"' \
  "$OUT/result.json" | sort -u > "$OUT/manifest-hashes.txt"
COUNT=$(wc -l < "$OUT/manifest-hashes.txt" | tr -d ' ')

ALL=true; : > "$OUT/downloads.tsv"
for f in "${WANT[@]}"; do
  call GET "/v1/jobs/$JOB/files/$f"
  mkdir -p "$OUT/files/$(dirname "$f")"; cp "$BODY" "$OUT/files/$f"
  h=$(tr -d '\r' < "$HDR" | awk -F': ' 'tolower($1)=="x-content-sha256"{print $2}')
  m=$(awk -v f="$f" '$1==f{print $2}' "$OUT/manifest-hashes.txt")
  l=$(sha "$OUT/files/$f")
  ok=$([ "$CODE" = 200 ] && [ "$h" = "$l" ] && [ "$m" = "$l" ] && echo true || echo false)
  [ "$ok" = true ] || ALL=false
  printf '%s\t%s\theader=%s\tmanifest=%s\tlocal=%s\tequal=%s\n' "$f" "$CODE" "$h" "$m" "$l" "$ok" >> "$OUT/downloads.tsv"
done
# path escape and unknown job are refused
call GET "/v1/jobs/$JOB/files/..%2Fstate.json"; ESC=$CODE
call GET /v1/jobs/job-00000000000000000000000000000000; UNK=$CODE

jq -n --arg host "$(hostname)" --arg base "$BASE" --arg key "$KEY" --arg in "$INPUT_SHA" \
  --arg started "$started" --arg finished "$(ts)" --arg job "$JOB" --arg trace "$TRACE" \
  --arg health "$HEALTH" --arg sc "$SUBMIT_CODE" --arg ss "$SUBMIT_STATUS" \
  --arg dc "$DUP_CODE" --argjson ds "$DUP_SAME" --arg cc "$CONF_CODE" --arg ce "$CONF_ERR" \
  --arg ec "$EARLY_CODE" --arg ee "$EARLY_ERR" --slurpfile final "$OUT/final-state.json" \
  --arg count "$COUNT" --arg esc "$ESC" --arg unk "$UNK" --argjson all "$ALL" \
  --rawfile dl "$OUT/downloads.tsv" '{
    client_host:$host, base_url:$base, idempotency_key:$key, input_sha256_sorted_json:$in,
    started:$started, finished:$finished, job_id:$job, trace_id:$trace, health:$health,
    submit:{http:$sc, status:$ss}, duplicate_submit:{http:$dc, same_job_id:$ds},
    conflict_submit:{http:$cc, error:$ce}, artifacts_before_done:{http:$ec, error:$ee},
    final_state:$final[0], manifest_artifact_count:($count|tonumber),
    downloads:($dl|split("\n")|map(select(length>0))), path_escape_http:$esc, unknown_job_http:$unk,
    ALL_DOWNLOADS_EQUAL:$all}' > "$OUT/summary.json"
cat "$OUT/summary.json"
