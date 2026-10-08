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
  and never add a key file by hand.
- Refounding is an acceptable cost. Changing geography requires one.
