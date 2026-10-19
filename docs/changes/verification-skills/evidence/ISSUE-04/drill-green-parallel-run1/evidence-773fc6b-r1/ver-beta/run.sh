#!/bin/bash
tag=$1; shift
{ printf '### %s\nSTART %s\nCMD %s\n' "$tag" "$(date -Is)" "$*"
  "$@" 2>&1
  printf 'EXIT %s\nEND %s\n' "$?" "$(date -Is)"
} | tee -a "$EVID/$tag.log"
