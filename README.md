# Interval: the window

The Unreal Engine window into [Interval](https://github.com/intervalplace/interval),
a world with a constitution instead of an owner.

The world is not here. Interval is a deterministic state machine and its spec
is the authority: the rules decide what is true, and every machine running them
computes the same world. This repository holds a way of LOOKING at that world,
and nothing in it can change what the world says. A window that disagrees with
the rules is a window that is wrong.

The live world is **Tallyholm**: [interval.place](https://interval.place).

## What a window has to do

Draw everything, and claim nothing it cannot draw.

Every word the world uses must have something to draw it, including the words a
node only BECOMES: a bellwork becomes a bell after twelve pulls, a spanwork
becomes a span after ten thousand planks, and neither is standing anywhere until
somebody does the work. A word the window cannot draw is a thing a citizen walks
past and never sees, which is worse than a thing drawn plainly.

`Tools/undrawn.py` asks that in all three directions: every word the world can
make, every word the window answers for that the world cannot make, and every
asset the look names. `Tools/audit_size.py` asks how big each of them actually
is, in metres.

The window also says so itself, once per word per rebuild, which is the report
worth trusting over any reading of the tables:

    grep "no mesh for it" /tmp/ue.log | sort -u

## What is in here

Everything in the project that was written: the plugin's C++, the shaders, the
art tables, the session tooling, the config, and the CC0 licence record for
every third-party asset. About six megabytes, and the only part that cannot be
rebuilt from something else.

- `Plugins/IntervalBridge/` the window itself, in C++
- `Tools/` the session tooling: `apply.py` lays the look into the asset,
  `cap.py` photographs the viewport, `sim.sh` and `play.sh` start a session
- `Tools/ground.hlsl`, `Tools/wall.hlsl` the ground and the cutaway
- `Art/*/README.md` where each third-party asset came from and under what
  licence, read from the asset's own page rather than inferred from a search
  filter

## What is not in here, and why

`Content/` is 857 MB of .uasset and `Art/` is 1.7 GB of source meshes. Git
without LFS handles neither well, and a repository that takes ten minutes to
clone is a repository nobody clones. So a clone of this will not build and run
on its own yet: it is the written part, kept because it is the part that cannot
be downloaded again. `.gitignore` says the same thing line by line, with the
reason beside each one.

There is a second reason, and it is the binding one. Not every pack in `Art/`
is CC0. The Bestiary kit is licensed under the Quaternius Asset License, which
allows using and modifying the models and shipping a built game that contains
them, with no fee or credit owed, but forbids redistributing the asset files
themselves. A repository carrying those raw files would be redistributing them.
So `Art/` stays out, and this is not a decision that size alone could reverse.

## Licence

The written work here is by Mats Julner.

Most of the third-party art is CC0, recorded per pack in `Art/*/README.md` with
the licence read from the asset's own page. The Bestiary kit is the exception
noted above and is NOT CC0. Nothing in this project should be described as CC0
wholesale.
