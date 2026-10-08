#!/bin/zsh
# BUILD THE iOS APP.
#
# The same shape as client.sh and for the same reasons; read that one first,
# because every trap it documents applies here too. What differs is why this
# exists at all.
#
# ON A PHONE THERE IS NO SECOND PROCESS. The desktop client is two pieces -- a
# window that holds only pixels and a Node bridge that holds the key and all
# world knowledge -- and iOS will neither ship Node nor let an app start an
# interpreter. So the bridge runs INSIDE the app, in JavaScriptCore, which iOS
# already has: see IntervalScript.h, and interval-bridge/portable/README.md
# where the whole thing is proven. `UIntervalBridgeSubsystem` defaults to
# `inproc` on this platform rather than dialling a loopback port that can never
# answer.
#
# AND THE RULES TRAVEL AS LOOSE FILES. `engine.js` is evaluated as text, byte
# for byte, because the SHA of those bytes is what a founding records about
# which rules made it -- so they are staged and never cooked. stage_bridge.sh
# puts them in Content/Bridge and checks that every import resolves.
#
#   ios.sh            -- stage, build, cook, package
#   ios.sh cook       -- skip the binary
#
# AND IF THE FULL RUN DIES AT "Failed to finalize the .app with Xcode":
#
# The build step ends in `ApplePostBuildSync`, which shells out to xcodebuild
# to assemble and sign the .app. Under UAT that has failed while the IDENTICAL
# xcodebuild command succeeds when run straight from a shell, and it fails
# silently: no `error:` line anywhere in the log, just two entries under "The
# following build commands failed", one of them a scheme PRE-action called
# "Touch UBT generated tiles" that exits 0 when run by hand. The named script
# is not the fault; Xcode reports it because the build around it failed.
#
# So do not go looking through that script. Run the finalize yourself:
#
#   UBT_NO_POST_DEPLOY=true xcodebuild build \
#     -workspace Intermediate/ProjectFiles/interval_IOS_interval.xcworkspace \
#     -scheme interval -configuration Development \
#     -destination generic/platform=iOS \
#     CODE_SIGN_ALLOW_ENTITLEMENTS_MODIFICATION=YES -allowProvisioningUpdates \
#     UE_XCODE_BUILD_MODE=PostBuildSync
#
# then `ios.sh cook`, which skips the binary and runs cook, stage and package
# against the .app that command just signed.
#
# AND UAT WRITES NO .ipa for this configuration. `-package` leaves a signed
# .app in Saved/StagedBuilds/IOS. An .ipa is a zip with the app inside a
# folder called Payload, and that is all it is:
#
#   mkdir -p /tmp/ipabuild/Payload
#   cp -R Saved/StagedBuilds/IOS/interval.app /tmp/ipabuild/Payload/
#   (cd /tmp/ipabuild && zip -qry "$P/interval-ios.ipa" Payload)
#
# To put it on a phone, plug the phone in and use
# `xcrun devicectl device install app --device <udid> interval-ios.ipa`.
# Dropping it into Finder's file-sharing tab does NOT install anything; that
# is document sharing, and the phone also needs Developer Mode turned on.
set -e
SP="$(cd "$(dirname "$0")" && pwd)"
P="$(dirname "$SP")"
UAT="/Users/Shared/Epic Games/UE_5.8/Engine/Build/BatchFiles/RunUAT.sh"

echo "--- the world's own rules, into the app"
zsh "$SP/stage_bridge.sh" | tail -2

# NOTHING ELSE MAY HOLD THE EDITOR OR ITS PORT; see the long note in client.sh.
pkill -f "UnrealEditor" 2>/dev/null || true
pkill -f "CrashReportClient" 2>/dev/null || true
sleep 3
for _ in $(seq 1 60); do
  lsof -nP -iTCP:8000 >/dev/null 2>&1 || break
  lsof -tnP -iTCP:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
  sleep 1
done

echo "--- cook, stage and package for iOS"
STEP=(-build -cook -stage -pak -package)
[ "$1" = "cook" ] && STEP=(-skipbuild -cook -stage -pak -package)
if ! "$UAT" BuildCookRun -project="$P/interval.uproject" -noP4 -platform=IOS \
     -clientconfig=Development "${STEP[@]}" -utf8output \
     > /tmp/interval-ios.log 2>&1; then
  echo "the iOS build failed. the last thing it said:"
  grep -iE "error|failed|codesign|provision" /tmp/interval-ios.log | tail -12
  echo "full log: /tmp/interval-ios.log"
  exit 1
fi
tail -3 /tmp/interval-ios.log
find "$P/Binaries/IOS" "$P/Saved/StagedBuilds/IOS" -name "*.ipa" 2>/dev/null | head
