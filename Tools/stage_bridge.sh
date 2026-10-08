#!/bin/zsh
# PUT THE WORLD'S OWN RULES INSIDE THE APP.
#
# On a desktop the bridge is a Node process beside the game and its files are
# the repository next door: `FIntervalScript::SourceRoot` finds
# `../interval-bridge` and reads them off the disk. A phone has no repository
# next door and no process beside anything, so the same files have to travel
# INSIDE the bundle -- and `Content/Bridge` is where SourceRoot looks when the
# repository is not there.
#
# THEY ARE NOT ASSETS AND MUST NOT BECOME ONE. `engine.js` is evaluated as
# text, byte for byte as it is on disk, because the SHA of those bytes is what
# a founding records about which rules made it. A cooked asset would be a
# different world and would say so in the one number that matters. So they are
# staged as loose files -- see `DirectoriesToAlwaysStageAsNonUFS` in
# DefaultGame.ini -- and read with the ordinary file layer.
#
#   stage_bridge.sh          -- copy and check
set -e
SP="$(cd "$(dirname "$0")" && pwd)"
P="$(dirname "$SP")"
B="$(dirname "$P")/interval-bridge"
OUT="$P/Content/Bridge"

rm -rf "$OUT"
mkdir -p "$OUT/portable" "$OUT/node_modules"

# THE SAME LIST THE PACKAGED DESKTOP CLIENT COPIES, minus the one thing a
# phone cannot use. `ws` is the Node WebSocket package; in the app the socket
# is Unreal's own and `host-node.mjs` only ever LINKS against `ws`, never calls
# it -- the shim answers an absent module with a proxy whose every function
# throws if anybody tries. So it is left out, and if that ever stops being
# true the failure is loud rather than silent.
cp "$B"/engine.js "$B"/sky.mjs "$B"/terrain-mirror.mjs "$B"/unreal-bridge.mjs \
   "$B"/host-node.mjs "$B"/view.mjs "$B"/worldgen*.mjs "$OUT/"
cp "$B"/portable/shim.js "$B"/portable/esm.js "$B"/portable/start.js \
   "$B"/portable/host-unreal.js "$OUT/portable/"
# ONLY ed25519, AND THAT IS THE WHOLE CRYPTO DEPENDENCY.
#
# `@noble` in the bridge's node_modules is four packages and a megabyte; the
# app needs one of them. The hashes are the PLATFORM'S -- `start.js` hands the
# shim `__digest`, which is CommonCrypto -- and the ciphers and the curves are
# never reached at all. Ed25519 is the one that cannot be the platform's,
# because Apple's own lives in CryptoKit and CryptoKit is Swift only.
mkdir -p "$OUT/node_modules/@noble"
cp -R "$B/node_modules/@noble/ed25519" "$OUT/node_modules/@noble/"

# AND CHECKED, because the list above is written by hand and the bridge grows.
# A missing file here is an app that starts, draws the title card, and never
# receives a frame -- with the reason in a JavaScript exception nobody on a
# phone can see.
python3 - "$OUT" "$B" <<'PYEOF'
import os, re, sys, hashlib
out, src = sys.argv[1], sys.argv[2]
have = set()
for root, _, files in os.walk(out):
    for f in files:
        have.add(os.path.relpath(os.path.join(root, f), out))

# ---- WHAT IS CHECKED, AND WHAT IS NOT ----
#
# The BRIDGE'S OWN modules, at the root, and nothing else. `node_modules` is a
# package's business and carries imports of source files that were never
# published; and `portable/esm.js` is the LOADER, whose own text is full of
# `from './x.mjs'` as documentation of what it resolves. Scanning either
# produces a page of confident nonsense, which is worse than not checking --
# the first version of this printed twelve missing files and every one of them
# was a comment or a package's own affair.
missing = []
for rel in sorted(have):
    if '/' in rel or not rel.endswith(('.mjs', '.js')):
        continue
    text = open(os.path.join(out, rel)).read()
    for m in re.finditer(r"^\s*import[^']*from\s+'(\.[^']+)'", text, re.M):
        want = os.path.normpath(m.group(1))
        if want not in have and want + '.js' not in have and want + '.mjs' not in have:
            missing.append((rel, m.group(1)))
for f, w in missing:
    print('  %s imports %s, which was not staged' % (f, w))
if missing:
    print('the staged bridge is short %d file(s); the app would draw nothing.' % len(missing))
    sys.exit(1)

# THE RULES ARE THE RULES, BYTE FOR BYTE, and this says so rather than hoping.
# A founding records the SHA of `engine.js`'s bytes; a copy that differed by a
# newline would be a different world and would say so in that one number.
here = hashlib.sha256(open(os.path.join(out, 'engine.js'), 'rb').read()).hexdigest()
there = hashlib.sha256(open(os.path.join(src, 'engine.js'), 'rb').read()).hexdigest()
if here != there:
    print('the staged engine.js is NOT the repository\'s: %s vs %s'
          % (here[:16], there[:16]))
    sys.exit(1)
print('staged %d files; engine.js is %s, the same bytes the desktop runs'
      % (len(have), here[:16]))
PYEOF
du -sh "$OUT"
