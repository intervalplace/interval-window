#!/bin/bash
# THE THREE DIRECTORIES GIT DOES NOT KEEP.
#
# `Art/` is the floor: nothing rebuilds it. The licence record in each
# `Art/*/README.md` says which pack it is and where it came from, so in
# principle most of it could be downloaded again -- but a pack that is
# re-downloaded later is not the same pack. `Art/Nature` is "the standard free
# version, 68 of 116 models", and a newer one would quietly change how the
# island looks. What is kept here is the exact art the world was built against.
#
# Two of the packs are paid and tied to an account rather than a public link:
# Bestiary and the Outfits source version.
#
# `Content/` is the imported form, which the `Tools/import_*.py` scripts build
# out of `Art/`. It is time rather than information, and it is copied anyway
# because that rebuild path has never been run end to end from nothing, and a
# route nobody has walked is not yet a way out.
#
# `Audio/` is small and its provenance has not been checked, so it comes too.
#
# NOT PUBLIC, EVER. `Art/Bestiary` is under the Quaternius Asset License, which
# allows shipping a built client containing the models and forbids
# redistributing the files themselves. A private copy is ordinary use. A public
# one is not. See `Art/Bestiary/README.md`.
#
#   Tools/backup.sh /Volumes/<drive>
#
# Additive on purpose: it never deletes at the far end. A backup that mirrors
# a deletion is not a backup of the thing that was deleted.
set -u
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-}"

if [ -z "$DEST" ]; then
  echo "where to? e.g. Tools/backup.sh /Volumes/MyDrive" >&2
  echo "mounted now:" >&2
  ls /Volumes/ >&2
  exit 2
fi
if [ ! -d "$DEST" ]; then
  echo "no such place: $DEST" >&2
  exit 2
fi

OUT="$DEST/interval-art-backup"
mkdir -p "$OUT" || exit 1

echo "from: $PROJ"
echo "to:   $OUT"
echo

for d in Art Audio Content; do
  [ -d "$PROJ/$d" ] || { echo "skip $d (not here)"; continue; }
  printf '%-8s %6s  ' "$d" "$(du -sh "$PROJ/$d" | cut -f1)"
  rsync -a --partial "$PROJ/$d/" "$OUT/$d/" && echo "copied" || { echo "FAILED"; exit 1; }
done

echo
echo "verifying by file count and size:"
for d in Art Audio Content; do
  [ -d "$PROJ/$d" ] || continue
  a=$(find "$PROJ/$d" -type f | wc -l | tr -d ' ')
  b=$(find "$OUT/$d" -type f | wc -l | tr -d ' ')
  as=$(du -sk "$PROJ/$d" | cut -f1)
  bs=$(du -sk "$OUT/$d" | cut -f1)
  if [ "$a" = "$b" ]; then
    printf '  %-8s %s files, %s MB  ok\n' "$d" "$a" "$((bs/1024))"
  else
    printf '  %-8s SOURCE %s files but COPY %s files  MISMATCH\n' "$d" "$a" "$b"
  fi
done

date -u +'%Y-%m-%dT%H:%M:%SZ' > "$OUT/last-backup.txt"
echo
echo "done. recorded in $OUT/last-backup.txt"
