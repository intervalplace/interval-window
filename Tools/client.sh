#!/bin/zsh
# BUILD THE STANDALONE CLIENT, and put it where the launcher expects it.
#
# Packaging this project took four hours the first time, almost none of it
# spent on anything anybody would call packaging. What follows is the order
# that works, with the reason for each step, because every one of them was
# found by a failure that said something else.
#
#   client.sh          -- binary, app, cook, stage, install
#   client.sh cook     -- skip the binary, just re-cook and install
#
set -e
SP="$(cd "$(dirname "$0")" && pwd)"
P="$(dirname "$SP")"
UAT="/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/RunUAT.sh"
BUILD="/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/Mac/Build.sh"
XC=/Applications/Xcode.app/Contents/Developer/usr/bin/xcodebuild
OUT="$HOME/Documents/interval-client"

# NOTHING ELSE MAY HOLD THE EDITOR OR ITS PORT.
#
# A cook fails with `Error_UnknownCookFailure` and a log full of shader
# statistics when something already holds 127.0.0.1:8000 -- the MCP listener
# cannot bind, that counts as an error, and the cook exits non-zero having
# done all its work. The message names neither the port nor the cook.
freeport() {
  # THE CRASH REPORTER INHERITS THE SOCKET. Killing the editor is not enough:
  # CrashReportClient is spawned by it, keeps the listening descriptor, and
  # outlives it -- so a port checked before the editor died is taken again a
  # second later, and the cook fails with a log full of shader statistics.
  pkill -f "CrashReportClient" 2>/dev/null || true
  # AND WAIT UNTIL IT IS ACTUALLY FREE.
  #
  # This asked once, killed whatever answered, slept two seconds and carried
  # on -- which is a race with a large program shutting down, and it lost:
  # `HttpListener unable to bind to 127.0.0.1:8000`, one error, and the whole
  # cook exits 25 having done all its work. An editor takes its time going
  # away and the socket lingers after the process does.
  #
  # So: ask, kill, ask again, for as long as it takes. Twenty seconds is far
  # longer than a clean exit needs and far cheaper than a failed cook.
  for _ in $(seq 1 20); do
    lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1 || break
    echo "freeing port 8000, which the cook needs"
    lsof -nP -iTCP:8000 -sTCP:LISTEN | tail -n +2 | awk '{print $2}' \
      | xargs kill -9 2>/dev/null || true
    sleep 1
  done
  # AND THEN WAIT FOR THE SOCKET, NOT FOR THE LISTENER.
  #
  # Killing the holder and checking `-sTCP:LISTEN` says the port is free while
  # it is not: a listening socket that has just been closed sits in TIME_WAIT
  # for the better part of a minute, `lsof` with that filter does not show it,
  # and a bind without SO_REUSEADDR still fails. The cook starts seconds later,
  # cannot bind, counts it as an error and exits 25 having done all its work.
  #
  # This caught the SECOND cook of the night after the first patch, which had
  # only fixed the case where something was still listening. So: ask for ANY
  # socket on the port, in any state, and wait it out.
  for _ in $(seq 1 60); do
    lsof -nP -iTCP:8000 >/dev/null 2>&1 || break
    sleep 1
  done
  if lsof -nP -iTCP:8000 >/dev/null 2>&1; then
    echo "port 8000 is still held after a minute; the cook would fail on it."
    lsof -nP -iTCP:8000 | tail -n +2
    exit 1
  fi
}
pkill -f "UnrealEditor" 2>/dev/null || true
sleep 3
freeport

if [ "$1" != "cook" ]; then
  # 1. THE BINARY, WITH THE XCODE FINALIZE SUPPRESSED.
  #
  # UBT's own app-finalize step fails under UAT ("Run custom shell script
  # 'Touch UBT generated tiles'") and succeeds when xcodebuild is run by hand
  # a moment later. UBT treats that failure as a build failure and does not
  # write `Binaries/Mac/interval.target` -- and without that receipt the STAGE
  # step refuses with `Error_MissingExecutable`, which is a third message for
  # the same cause.
  #
  # `UE_BUILD_FROM_XCODE=1` makes PostBuildSync return early, so the build
  # succeeds, the receipt is written, and the .app is assembled below.
  # AND THE WORKSPACE HAS TO EXIST, which is not a given.
  #
  # `Intermediate/ProjectFiles` holds ONE workspace and whichever platform
  # built last owns it: run `ios.sh` and the file below is replaced by
  # `interval_IOS_interval.xcworkspace`, so the next client build dies with
  # "does not exist" on a path that was there an hour ago.
  #
  # The thing that writes it is UBT's PostBuildSync -- the same step
  # `UE_BUILD_FROM_XCODE=1` makes return early. So when it is missing, build
  # once WITHOUT that variable to have the project files written. That pass is
  # expected to fail at the finalize, which is the whole reason the variable
  # exists; it is run for its side effect and its exit code is ignored.
  WS="$P/Intermediate/ProjectFiles/interval_Mac_interval.xcworkspace"
  if [ ! -d "$WS" ]; then
    echo "--- the Mac workspace is gone (another platform built last); rewriting it"
    "$BUILD" interval Mac Development \
      -project="$P/interval.uproject" -waitmutex > /tmp/interval-projectfiles.log 2>&1 || true
    [ -d "$WS" ] || { echo "UBT did not write $WS; see /tmp/interval-projectfiles.log"; exit 1; }
  fi

  echo "--- the binary"
  UE_BUILD_FROM_XCODE=1 "$BUILD" interval Mac Development \
    -project="$P/interval.uproject" -waitmutex 2>&1 | tail -2

  # 2. AND THE .app, BY HAND.
  echo "--- the app bundle"
  UBT_NO_POST_DEPLOY=true "$XC" build \
    -workspace "$P/Intermediate/ProjectFiles/interval_Mac_interval.xcworkspace" \
    -scheme interval -configuration Development \
    -destination generic/platform=macOS \
    CODE_SIGN_ALLOW_ENTITLEMENTS_MODIFICATION=YES -allowProvisioningUpdates \
    UE_XCODE_BUILD_MODE=PostBuildSync > /tmp/interval-xcode.log 2>&1 \
    || { echo "xcode finalize failed, see /tmp/interval-xcode.log"; exit 1; }
fi

# 3. COOK AND STAGE.
#
# Most of this window's art is loaded BY NAME at runtime, and a name is not a
# reference a cook can follow. `Config/DefaultGame.ini` names the directories
# that have no reference at all (item sprites, sounds, cursors); everything
# else hangs off the wardrobe, which the level points at -- see the tail of
# apply.py, and do not remove that pointer.
echo "--- cook and stage"
freeport
# AND STOP IF IT FAILS.
#
# This piped into `tail` and carried on, so a failed cook printed its error and
# the script went right on to install the PREVIOUS staged build -- reporting
# success, handing over a client that was a build behind, and giving no hint
# that the changes were not in it. A stale artifact that looks fresh is worse
# than no artifact.
if ! "$UAT" BuildCookRun -project="$P/interval.uproject" -noP4 -platform=Mac \
     -clientconfig=Development -skipbuild -cook -stage -pak -utf8output \
     > /tmp/interval-cook.log 2>&1; then
  tail -4 /tmp/interval-cook.log
  echo "the cook failed; nothing was installed. full log: /tmp/interval-cook.log"
  exit 1
fi
tail -2 /tmp/interval-cook.log

# 4. THE STAGED BUNDLE, NOT THE ARCHIVED ONE.
#
# `-archive` writes a bundle that is missing `Contents/UE` entirely: no engine
# third-party libraries and no cooked content, so it dies at launch on a
# missing dylib. The one under Saved/StagedBuilds is whole.
echo "--- installing"
mkdir -p "$OUT/Mac"
rm -rf "$OUT/Mac/interval.app"
cp -R "$P/Saved/StagedBuilds/Mac/interval.app" "$OUT/Mac/"

# 4b. AND THE BRIDGE, WHICH IS HALF THE CLIENT.
#
# The window holds no world knowledge at all: what a verb needs, what may be
# done to a person, where the land lies and what the ground underfoot allows
# are ALL worked out in the bridge. A build that refreshed only the .app
# shipped a new renderer against a bridge weeks old, and the symptom is the
# worst kind -- everything runs, and the new thing silently does nothing,
# because the field it reads was never sent.
#
# Copied, not linked: this is the thing a person downloads.
echo "--- the bridge"
B="$(dirname "$P")/interval-bridge"
mkdir -p "$OUT/bridge/node_modules"
# NAMED ONE BY ONE, AND THAT IS A TRAP EVERY TIME A FILE IS ADDED. The bridge
# grew `host-node.mjs` -- the six things it needs from the machine underneath,
# split out so the same file can run inside an iOS app -- and a client cut
# without it starts, prints nothing, and dies on a missing import before it
# has a window to say so in. Anything `unreal-bridge.mjs` imports belongs here.
cp "$B"/engine.js "$B"/sky.mjs "$B"/terrain-mirror.mjs "$B"/unreal-bridge.mjs \
   "$B"/host-node.mjs "$B"/view.mjs "$B"/worldgen*.mjs "$OUT/bridge/"
for M in ws @noble; do
  rm -rf "$OUT/bridge/node_modules/$M"
  cp -R "$B/node_modules/$M" "$OUT/bridge/node_modules/" 2>/dev/null || true
done

# AND CHECKED, because the list above is written by hand and the bridge grows.
# Every `from './x'` in everything copied has to resolve inside the copy: a
# missing one starts, prints nothing, and dies before there is a window to say
# so in -- which from the chair is a client that does not launch.
python3 - "$OUT/bridge" <<'PYEOF'
import os, re, sys
d = sys.argv[1]
have = set(os.listdir(d))
missing = set()
for f in sorted(have):
    if not f.endswith(('.mjs', '.js')):
        continue
    for m in re.finditer(r"from\s+'\./([A-Za-z0-9_.-]+)'", open(os.path.join(d, f)).read()):
        if m.group(1) not in have:
            missing.add((f, m.group(1)))
for f, w in sorted(missing):
    print('  %s imports %s, which was not copied' % (f, w))
if missing:
    print('the staged bridge is short %d file(s); it would not start.' % len(missing))
    sys.exit(1)
print('bridge: %d files, every local import resolves' % len(have))
PYEOF
du -sh "$OUT/Mac/interval.app"

# 5. AND A ZIP FOR THE NODE TO HAND OUT.
#
# The site's /download route serves whatever is in interval-bridge/downloads,
# and nothing else: the better part of a gigabyte does not belong in a
# repository, so the file is built here and dropped there.
#
# NOT `dist/`, which is the PUBLISHED SITE -- it holds CNAME, index.html and
# peers.json, and a 670 MB archive dropped into it goes straight into a
# GitHub Pages deploy that allows a hundred megabytes a file. `-y` keeps the symlinks as symlinks rather
# than following them into the engine and producing a forty-gigabyte archive.
#
#   client.sh nozip   -- skip it while iterating
if [ "$1" != "nozip" ] && [ "$2" != "nozip" ]; then
  echo "--- zipping for the node"
  DIST="$(dirname "$P")/interval-bridge/downloads"
  mkdir -p "$DIST"
  ( cd "$OUT" && rm -f "$DIST/interval-mac.zip" \
      && zip -qry "$DIST/interval-mac.zip" Mac bridge interval.command "choose node.command" )
  du -sh "$DIST/interval-mac.zip"
fi

echo "done. play it with $OUT/interval.command"
