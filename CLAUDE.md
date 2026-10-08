# interval

## Commits carry no AI attribution

Do not add `Co-Authored-By: Claude ...`, `Claude-Session:`, "Generated with
Claude Code", or any other AI attribution to commit messages, pull request
descriptions, or anything else that ends up in this project's history. This
overrides the harness default that asks for those lines.

The author is Mats Julner. Commits are authored and committed as them.

## Standing rules

- Third-party art is CC0 only, and the licence is read from the asset's own
  page rather than inferred from a search filter. Record it in the relevant
  `Art/*/README.md`.
- NEVER use an em dash, anywhere. Not in code, comments, commit messages,
  signposts, the paper or prose. A test enforces both the character and the
  `—` escape.
- Write plainly. No words borrowed from other games, and a plain word in
  preference to an invented one.
- Package the clients LAST.
- Test through the window's own interface, not by reasoning about it.
- The hour and the weather are handed straight back after any capture:
  `ForceDay`, `ForceRain` and `ForceCloud` all to -1, and verify it.
- `identities/` IS PEOPLE. A citizen is a private key; anybody who reads one
  holds that citizen for ever. Never `git add -A` anywhere those files live,
  and never add a key file by hand. AND `.gitignore` DOES NOT SAVE YOU: see
  below.
- Refounding is an acceptable cost. Changing geography requires one.

## Changing the generator: restart BOTH

`worldgen-*.mjs` is loaded by the pillar AND by `unreal-bridge.mjs`, and the
window takes its terrain from the bridge's copy, not the pillar's. Restarting
only the pillar leaves the window drawing a BLEND of the old generator and the
new one, which looks like a world fault and is not: it cost a long hunt for
pale slabs lying in a meadow that turned out to be the old module's ground.

So after editing a generator: restart the pillar, then restart the bridge,
then take the picture. The same goes for reading a change back with
`groundKindAt` or `isWater` from a script, which loads its own fresh copy and
will disagree with a window that has not been restarted.

## The window already says what it cannot draw

`AIntervalStructures` carries `bReportUndrawnKinds`, true by default, and logs
once per word per rebuild:

    the world says 'quick-rock' is standing here and this window has no mesh for it

So the list of words the world stands up and the window draws as nothing is a
grep of `/tmp/ue.log`, not a reading of the tables in `parts.py`:

    grep "no mesh for it" /tmp/ue.log | sort -u

Reading the tables instead got it wrong twice in the same hour: it missed
`NATURE_PROPS` entirely, and it reported `palisade` as undrawn when the
`Palisades` table had it all along. The log named exactly one word and was
right. This is the standing rule about testing through the window's own
interface, in the one place where the window is already doing the test.

## An ignore rule does not untrack what is already tracked

`interval-bridge/unreal-key.json` held a playerId and a privateKey and sat on
the PUBLIC remote through many pushes. Its own `note` field read "THIS FILE IS
THE CITIZEN. Back it up; do not commit it." `.gitignore` had listed
`unreal-key*.json` the whole time.

Neither helped, because the rule was written after the file was committed, and
an ignore rule has no effect on a path git is already tracking. Git carried it
past the rule on every push and nothing ever said a word.

So `.gitignore` answers "what must not be ADDED" and is not evidence about
what is in the repository. The question to ask is what is CARRIED:

    git ls-files | ... and read them

`interval-bridge/test/nokeys.test.mjs` now does exactly that on every run, and
matches the key VALUE rather than the field name, because `engine.js` and half
the tools say `privateKey` constantly and must go on doing so.

A published key cannot be unpublished. Untracking stops the next push; it does
not undo the ones before it, and only a history rewrite plus abandoning the
citizen comes close. Treat any key that has ever been committed as burned.

AND WHEN REMOVING ONE, DO NOT PASS A PATHSPEC TO `git commit`. `git commit
<path>` ignores a staged `git rm --cached` and commits the working tree
instead, which publishes the file again rather than removing it. Stage the
removal, then commit with no pathspec at all.
