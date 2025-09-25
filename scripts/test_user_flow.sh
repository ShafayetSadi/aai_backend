#!/usr/bin/env bash
set -euo pipefail

API="http://127.0.0.1:8000/api/v1"
TMP=$(mktemp -d)
echo "Working in $TMP"

######################################
# Feature Flags (set true/false)
######################################
DO_REGISTER_MANAGER=false
DO_REGISTER_STAFF=false
DO_CREATE_ORG=false
DO_CREATE_ROLE=false
DO_CREATE_SHIFT=false
DO_CREATE_REQUIREMENTS=true
DO_CREATE_SCHEDULE=false
DO_INVITE_STAFF=false
DO_UPDATE_AVAILABILITY=false
DO_VIEW_SCHEDULE=false

# Helper to assert HTTP status (accepts multiple)
assert_status() {
  local expected="$1"
  local got="$2"
  local msg="$3"
  if [[ ! " $expected " =~ " $got " ]]; then
    echo "❌ FAIL: $msg (expected one of [$expected], got $got)"
    exit 1
  fi
}

# Helper to extract JSON field
jq_get() { jq -r "$1" <<< "$2"; }

# Helper to run curl, capture json + status, print nicely
do_curl() {
  local method="$1"; shift
  local url="$1"; shift
  local msg="$1"; shift
  local expected="$1"; shift

  RESP=$(curl -s -w "\n%{http_code}" -X "$method" "$url" "$@")
  JSON=$(head -n -1 <<< "$RESP")
  STATUS=$(tail -n1 <<< "$RESP")

  # Pretty output -> stderr
  {
    echo -e "\n--- $msg (status: $STATUS) ---"
    if [[ -n "$JSON" && "$JSON" != "null" ]]; then
      echo "$JSON" | jq .
    else
      echo "{}"
    fi
    echo ""   # spacing between steps
    echo ""
  } >&2

  assert_status "$expected" "$STATUS" "$msg"

  # Raw JSON returned for capture
  printf '%s' "$JSON"
}

######################################
# 1. Register and login manager
######################################
if $DO_REGISTER_MANAGER; then
  do_curl POST "$API/auth/register" "Register Manager" "200 400 422" \
    -H "Content-Type: application/json" \
    -d '{"email":"manager@example.com","username":"manager","password":"Pass1234"}'
fi

MANAGER_LOGIN=$(do_curl POST "$API/auth/login" "Login Manager" "200 400 422" \
  -H "Content-Type: application/json" \
  -d '{"email":"manager@example.com","password":"Pass1234"}')
MANAGER_TOKEN=$(jq_get .access_token "$MANAGER_LOGIN")

######################################
# 2. Register and login staff
######################################
if $DO_REGISTER_STAFF; then
  do_curl POST "$API/auth/register" "Register Staff" "200 400 422" \
    -H "Content-Type: application/json" \
    -d '{"email":"staff@example.com","username":"staff","password":"Pass1234"}'
fi

STAFF_LOGIN=$(do_curl POST "$API/auth/login" "Login Staff" "200 400 422" \
  -H "Content-Type: application/json" \
  -d '{"email":"staff@example.com","password":"Pass1234"}')
STAFF_TOKEN=$(jq_get .access_token "$STAFF_LOGIN")

######################################
# 3. Manager creates or fetches organization
######################################
if $DO_CREATE_ORG; then
  ORG_JSON=$(do_curl POST "$API/organizations" "Create Organization" "200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test Restaurant"}')
  ORG_ID=$(jq_get .id "$ORG_JSON")
fi

if [[ -z "${ORG_ID:-}" || "$ORG_ID" == "null" ]]; then
  ORG_LIST=$(do_curl GET "$API/organizations" "List Organizations" "200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN")
  ORG_ID=$(jq_get '.organizations[0].id' "$ORG_LIST")
fi

if [[ "$ORG_ID" == "null" || -z "$ORG_ID" ]]; then
  echo "❌ ERROR: No organization found."
  exit 1
fi
echo "✅ ORG_ID=$ORG_ID"

######################################
# 4. Manager creates or fetches role
######################################
if $DO_CREATE_ROLE; then
  ROLE_JSON=$(do_curl POST "$API/organizations/$ORG_ID/roles/" "Create Role" "201 200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"Chef"}')
  ROLE_ID=$(jq_get .id "$ROLE_JSON")
fi

if [[ -z "${ROLE_ID:-}" || "$ROLE_ID" == "null" ]]; then
  ROLE_LIST=$(do_curl GET "$API/organizations/$ORG_ID/roles/" "List Roles" "200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN")
  ROLE_ID=$(jq_get '.roles[0].id' "$ROLE_LIST")
fi

if [[ "$ROLE_ID" == "null" || -z "$ROLE_ID" ]]; then
  echo "❌ ERROR: No role found."
  exit 1
fi
echo "✅ ROLE_ID=$ROLE_ID"

######################################
# 5. Manager creates or fetches shift template
######################################
if $DO_CREATE_SHIFT; then
  SHIFT_JSON=$(do_curl POST "$API/organizations/$ORG_ID/shift-templates/" "Create Shift Template" "201 200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"Morning","start_time":"09:00:00","end_time":"17:00:00"}')
  SHIFT_ID=$(jq_get .id "$SHIFT_JSON")
fi

if [[ -z "${SHIFT_ID:-}" || "$SHIFT_ID" == "null" ]]; then
  SHIFT_LIST=$(do_curl GET "$API/organizations/$ORG_ID/shift-templates/" "List Shift Templates" "200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN")
  SHIFT_ID=$(jq_get '.shift_templates[0].id' "$SHIFT_LIST")
fi

if [[ "$SHIFT_ID" == "null" || -z "$SHIFT_ID" ]]; then
  echo "❌ ERROR: No shift template found."
  exit 1
fi
echo "✅ SHIFT_ID=$SHIFT_ID"

######################################
# 6. Manager creates or fetches requirement template + items
######################################
if $DO_CREATE_REQUIREMENTS; then
  REQT_JSON=$(do_curl POST "$API/organizations/$ORG_ID/requirement-templates/" "Create Requirement Template" "201 200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"Weekly Requirements"}')
  REQT_ID=$(jq_get .id "$REQT_JSON")

  do_curl PUT "$API/organizations/$ORG_ID/requirement-templates/$REQT_ID/items" "Add Requirement Items" "200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"items":[{"weekday":1,"shift_template_id":"'$SHIFT_ID'","role_id":"'$ROLE_ID'","required_count":1}]}'
fi

if [[ -z "${REQT_ID:-}" || "$REQT_ID" == "null" ]]; then
  REQT_LIST=$(do_curl GET "$API/organizations/$ORG_ID/requirement-templates/" "List Requirement Templates" "200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN")
  REQT_ID=$(jq_get '.requirement_templates[0].id' "$REQT_LIST")
fi

if [[ "$REQT_ID" == "null" || -z "$REQT_ID" ]]; then
  echo "❌ ERROR: No requirement template found."
  exit 1
fi
echo "✅ REQT_ID=$REQT_ID"

######################################
# 7. Manager creates or fetches schedule
######################################
if $DO_CREATE_SCHEDULE; then
  SCHED_JSON=$(do_curl POST "$API/organizations/$ORG_ID/schedules/" "Create Schedule" "201 200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"week_start":"2025-09-29","organization_id":"'$ORG_ID'","source_requirement_template_id":"'$REQT_ID'"}')
  SCHED_ID=$(jq_get .id "$SCHED_JSON")

  do_curl POST "$API/organizations/$ORG_ID/schedules/$SCHED_ID/auto-assign" "Auto-Assign Schedule" "200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN"

  do_curl POST "$API/organizations/$ORG_ID/schedules/$SCHED_ID/publish" "Publish Schedule" "200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN"
fi

if [[ -z "${SCHED_ID:-}" || "$SCHED_ID" == "null" ]]; then
  SCHED_LIST=$(do_curl GET "$API/organizations/$ORG_ID/schedules/" "List Schedules" "200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN")
  SCHED_ID=$(jq_get '.schedules[0].id' "$SCHED_LIST")
fi

if [[ "$SCHED_ID" == "null" || -z "$SCHED_ID" ]]; then
  echo "❌ ERROR: No schedule found."
  exit 1
fi
echo "✅ SCHED_ID=$SCHED_ID"

######################################
# 8. Manager invites staff
######################################
if $DO_INVITE_STAFF; then
  STAFF_USER=$(do_curl GET "$API/me" "Get Staff User" "200 400 422" -H "Authorization: Bearer $STAFF_TOKEN")
  STAFF_UID=$(jq_get .id "$STAFF_USER")

  do_curl POST "$API/organizations/$ORG_ID/invite" "Invite Staff" "204 200 400 422" \
    -H "Authorization: Bearer $MANAGER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"'$STAFF_UID'","role":"staff"}'
fi

######################################
# 9. Staff updates availability
######################################
if $DO_UPDATE_AVAILABILITY; then
  do_curl PATCH "$API/me/availability" "Update Staff Availability" "204 200 400 422" \
    -H "Authorization: Bearer $STAFF_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"day":"monday","available":true}'
fi

######################################
# 10. Staff views schedule
######################################
if $DO_VIEW_SCHEDULE; then
  do_curl GET "$API/me/schedule" "View Staff Schedule" "200 400 422" \
    -H "Authorization: Bearer $STAFF_TOKEN"
fi
