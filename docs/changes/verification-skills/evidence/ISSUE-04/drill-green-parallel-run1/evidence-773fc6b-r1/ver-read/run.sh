#!/bin/bash
EVID=/tmp/orchestra-04/parallel/docs/changes/relay-board/evidence-773fc6b-r1/ver-read
tag=$1; shift
{ printf '### %s\nSTART %s\nCMD %s\n' "$tag" "$(date -Is)" "$*"
  "$@" 2>&1
  printf 'EXIT %s\nEND %s\n' "$?" "$(date -Is)"
} | tee -a "$EVID/$tag.log"
