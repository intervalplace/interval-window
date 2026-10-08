# Found by playing

Defects and gaps found by walking a citizen through the world and interacting
with things, rather than by reading the code. Kept here so a play session can
report a fault and carry on instead of stopping to fix each one.

Each entry says what was seen, what causes it, and what fixing it means. A
thing is only struck off when it has been seen working **in the world**, not
when the code looks right.

---

## Open

### THE GROUND MATERIAL WAS NOT COMPILING, AND NOTHING SAID SO

Worth reading before anything else in this file, because it invalidated most
of an afternoon's work and it will do it again.

`Tools/ground.hlsl` is compiled into `M_IntervalGround`. On Metal that
material is compiled once per permutation, and two of those permutations are
RAY TRACING hit shaders -- `TMaterialCHS` and `FPathTracingMaterialCHS` --
which this window never draws a pixel with. If one of them fails, Unreal marks
the WHOLE MATERIAL as failed, **keeps the last shader map that did compile, and
carries on rendering with it.** No red, no default grey, no warning in the
viewport. The material asset on disk is correct, the graph is correct, the
editor reports the right parameters, and the screen shows a build of the
shader from hours ago.

The symptom is that edits to this file do nothing. It was diagnosed only by
tinting the entire ground pink and watching nothing happen -- which is the
right move and should be the FIRST move next time an edit to this file appears
to have no effect.

The trigger was:

    if (Ln > 0.00001) Edge = min(Edge, dot(..., Dv * rsqrt(Ln)));

`rsqrt` under a branch, inside an unrolled loop, in a ray-tracing hit shader.
MetalShaderConverter rejects it with **"Unhandled FP64 usage"**, which names
neither the line nor anything true about the code. The same arithmetic written
branchless, with `/ sqrt(Ln)` and a select, compiles clean.

**So: `make_ground.py` prints `compile:` and it must say `clean`.** An error
line there is not a warning about a feature nobody uses. It means every
subsequent edit to the ground is being silently discarded.

### AND THE ORDER IS STILL: MAKE, RESTART, APPLY

`Tools/rebuild.sh` documents this and it was walked into anyway. `make_ground.py`
DELETES the material and builds a new one at the same path; the ground actor in
the level and the look asset still hold the old, now-trashed object. Running
`apply.py` before restarting the editor copies that dead pointer into the look,
so the saved asset points at nothing that will ever be drawn again.

Running `apply.py` immediately after `make_ground.py`, as that script's own
closing line suggests, is only safe if the editor is restarted in between.

### A REFUSED DEED STILL ANIMATES

`UIntervalBridgeSubsystem::Doing` remembers what the hand filed and holds the
motion for 1.15 seconds, which is what gives the instant deeds a body at all.
It does not yet know whether the WORLD took the deed. A refusal shows up only
as `lastInput` failing to advance, and by the time that can be known the beat
is nearly over -- so for about a second the citizen mimes a deed that did not
happen. Nothing else in this window invents world state and this does, a
little. The honest fix is to record the tick a deed was filed at and cut the
motion when the next frame shows `lastInput` behind it.

### THE KEEPERS' KIT IS STILL PRIMITIVES, AND IT SHOWS

A keeper at a well, photographed from the watch camera, is a wide flat disc
with boots under it and a pole across it. Both are correct geometry seen from
almost overhead: `hat(CONE, THATCH, 0.90, ...)` is a brim NINETY CENTIMETRES
across on a person fifty centimetres wide, and the staff is an eight-centimetre
cylinder standing vertically, which at this camera projects as a line lying
over the body.

So nothing is broken and it still reads as nonsense. The brims are simply far
too wide -- a straw hat is about half that -- but the real answer is real art:
this project already imports CC0 character kits, and a hat and a staff from one
would end the question rather than shrink it.


### Nothing a citizen MAKES has an animation
Fishing has one -- `gather.fishing-spot` plays `Fixing_Kneeling` at half speed
with a rod in hand, a kneel at the water's edge -- because it is a `gather`,
and gathers are keyed by the node they work.

Every INSTANT deed plays nothing at all. The whole motion table is `still`,
`walk`, `gather`, `attack`, `attackp`, `raise`, `felled`, `hurt`, plus the
per-node gathers. So a citizen cooking a fish, fletching a bow, transmuting a
log, planting a field, smithing, eating or picking something up simply stands
there while the item changes in their pack. Thirty-odd verbs, no gesture
between them.
This is the same shape as the gap that was closed for keepers' kit and for the
verbs themselves: the thing HAPPENS and the window says nothing. The pack
proves it worked; the world does not show it.

### The south-east of the island renders as a flat red-brown void
Everywhere south of about row 320 on the east side -- 621,324 at the South
Pass, and 632,336 / 641,343 / 645,340 near Eastmere -- the whole viewport is
one uniform dark red-brown with the citizen's name plate floating in it. No
ground detail, no scatter, no chalk roads, no citizen body, no props. The
PANEL and the feed draw perfectly on top of it, so the window is running.

WHAT IT IS NOT, each ruled out by measurement rather than argument:
  * not night -- the sky says `elevDeg 30.7`, `dayAmt 1`, broad overcast day.
  * not streaming -- `IntervalChunk_79` and `_80` exist at the citizen's feet
    with their `Ground`, `Roofs` and four scatter components, `bVisible` true
    and `bHiddenInGame` false.
  * not the camera -- read off `CameraActor_0`, it sits at 128202,67380,1380
    pitched -50 degrees, which is exactly WatchReach/WatchRise behind and above
    the citizen. Where it should be, above the ground, looking at them.
  * not transient -- walking thirteen tiles and restarting the play session
    entirely both leave it unchanged.
  * not the season, though it turned to winter between the good frames and the
    bad ones: the frame carries `spring`, `autumn` and `winter` and nothing in
    the window reads them.
  * not fog, not volumetric fog, not post-processing -- each disabled in turn
    through the new `exec` verb, and the red survives all three.
  * and NOT the ground colour table: `downs` is `L[24]`, a yellow-green
    (0.250, 0.290, 0.140), and `chalk` is `L[7]`, near-white. The soil here is
    downs and chalk, and the chalk roads run right through the frame.

WHAT IT IS. `viewmode unlit` -- raw base colour, no lighting -- shows the SAME
red-brown, carrying the ground shader's own two-scale grain mottle. So this is
the ground, drawing a brown, with its albedo coming out of the colour table at
an index that is not the one the bridge says. The strongest clue is what is
MISSING: no chalk road lightening the path, and no scatter at all. A chunk
whose codes were uniform would look exactly like this -- one flat colour, no
road, and scatter only for that one code. `trail` is code 1, its colour
(0.230, 0.165, 0.100) is a brown, and it is one of the few grounds with no
scatter entry at all.
AND IT IS REGIONAL, NOT GLOBAL. A citizen born at Anchor immediately
afterwards stands in a perfectly drawn town -- daylight, timber framing,
cobbles, varied grass, a shadow under their feet. So nothing global is broken;
the south-east specifically is.
THE BRIDGE'S DATA IS ALSO FINE. The chunk the window would ask for --
64x64 with a skirt at 576,320, the one containing all four red positions --
comes back 4356 bytes for 4356 tiles, every plane the same length, and its
codes are 4032 `downs`, 152 `chalk`, 130 `trail`, and a scattering of flag,
floor and gravel. Exactly the country the map shows. So the bridge sends the
right ground and the window draws a different one.
IT IS THE SKY, NOT THE GROUND. Measured rather than judged: the patch reads
sRGB (0.527, 0.279, 0.260), a linear hue ratio of 1 : 0.26 : 0.23, and NOTHING
in the ground shader can make that. The colour table's reddest entries sit near
1 : 0.70 : 0.42, and neither the verge blend nor the worn-way colour goes
redder. What is actually in front of the camera is `StaticMeshActor_0` --
`/Engine/EngineSky/SM_SkySphere` at scale 400 -- seen from INSIDE its lower
half, with the SkyAtmosphere behind it: hiding the sphere darkens the frame and
leaves the rest. That is why no toggle touched it. Fog, volumetric fog and
post-processing are irrelevant to an unlit sky.
SO THE GROUND SIMPLY IS NOT DRAWN HERE, and the question is why. Everything
checks out on inspection: `IntervalChunk_79` sits at exactly 115200,64000 =
tile 576,320, its `Ground` component is `bVisible` true, `bHiddenInGame` false,
`bRenderInMainPass` true with no draw-distance cap, the control texture is
66x66 = 4356 texels for 4356 tiles, and `Build` logs no error, so the
`Codes.Num() != Expected` guard passed and `BuildMesh` ran.
AND THE GROUND IS THERE. `showflag.Wireframe 1` fills the frame with solid
edges -- dense geometry directly in front of the camera -- with the scatter's
own wireframe specks in it. So the mesh exists, is in view, and is not culled.
EVERY INPUT IS CORRECT, each one checked rather than assumed:
  * the chunk containing the citizen sits at exactly the right tile, and its
    `Ground` is visible, unhidden, in the main pass, with no draw-distance cap.
  * the material is `M_IntervalGround` through a MID on the component, the same
    material that draws Anchor correctly in the SAME session.
  * the CODES are right. A temporary histogram at the moment the control
    texture is packed prints `chunk 576,320 codes: 24 x4782  7 x178  1 x138` --
    downs, chalk and trail, exactly the country the map shows. The window is
    not being lied to.
  * the camera is at 125603,62181,1380 pitched -50, which is WatchReach and
    WatchRise behind and above the citizen to the centimetre.
  * and a citizen standing at Anchor in the same play session, on the same
    build, sees a perfectly drawn town.
So: right data, right geometry, right material, right camera -- and a quarter
of the island draws as the inside of the sky sphere. The fault is between the
control texture and the pixel, and nothing about the inputs will find it. The
next thing to try is the material itself: read the MID's `Control` parameter
back and sample it, or bisect `ground.hlsl` by returning the raw code as a
colour and seeing whether the shader agrees with the histogram.

ONE REAL BUG WAS FOUND ON THE WAY AND IS FIXED. `Want()` refused to ask for a
chunk already in `Pending`, and the only thing that ever cleared `Pending` was
the reply ARRIVING. A reply that never came -- the bridge restarted with
requests in flight, which happened a dozen times in this session -- stranded
that ground for the life of the play session: never asked for again, never
built. `Pending` carries the time it was asked now, a request unanswered for
four seconds is asked again, and `HandleFrame` no longer returns early while
anything is stale, so a citizen standing still in a hole gets their ground
back rather than standing in it for ever.

### The horse question is open
The user asked for a mount while hauling. **The world has no horse**: the only
match in the engine is `sawhorse`, and `cart` is a node type for what a dead
hauler *spills*. The constitution names the trade RUNNER rather than carter
deliberately -- "this citizen walks the roads with what somebody paid them to
walk it with, under the one law in the world that lets anybody strike them for
it (§11d)". A mount would remove the risk that rule exists to create. The load
is drawn on the runner's back in the meantime; the horse is the user's call,
and the art for one exists.

---

---

## Found in the WORLD, not in the window

Things this window cannot fix, because the engine it mirrors has to match the
world's own consensus byte for byte. Written down because playing found them
and because somebody who owns the world may want them.

### A fire arrow cannot be fletched
`fletch` with `make: 'fire-arrows'` is refused before any rule is consulted.
The recipe is real everywhere else: the VALIDATOR has a branch for it (four
shafts, a measure of brimstone, woodcraft 24) and the EXECUTOR has the effect
(it consumes them and pays double experience). What it has not got is a SHAPE
-- `T.make` is a hardcoded list of eleven words and `fire-arrows` is not among
them, so `normalizeInput` rejects it at the door.
This is the exact fault the engine's own note describes a few lines above the
list: "A verb needs three things to exist: a shape in this table, a rule in
validate(), and an effect in apply(). `drink` and `set_look` were given the
last two and not the first." It happened again, to a `make` rather than to a
verb. `T.recipe` cannot drift this way because it looks its words up in
RECIPES; `T.make` and `T.spell` are hand-written lists and can.

---

## Fixed, and seen working in the world

### The streets of Anchor are paved, and were poured concrete

`cobble`, `flag` and `plaza` were three flat greys with the common mottle over
them, which at this camera is a slab of concrete with a road painted on it.
Reported plainly: *"i think cobblestone (if that is what the road inside anchor
is) could be more detailed, now it just looks like concrete."*

Asked what it is standing on, the world answers `flag` down the length of the
street, `cobbl` where the ways cross, and `floor` inside the houses. Three
words, three trades, one colour.

Now: flag and plaza are a jittered brick grid in a running bond, cobble is
cellular -- one found stone per cell, nearest wins, so the stones are all
different shapes and still tile the plane with no gaps. Each stone gets its own
grey, one in eight is a different rock, the joints hold dirt rather than
shadow, and the face of a stone slopes away at the joint so a cobble is a dome
and a slab has its edges knocked off.

Two things were got wrong first and both were found by photographing them:

* **A running bond in a Voronoi is a HONEYCOMB.** A square lattice with every
  other row shifted by half IS a hexagonal lattice, so every street in Anchor
  came out as hexagonal concrete pavers -- the exact look the work was meant to
  remove. Slabs are cut, not found, so they do not want cells at all; a
  jittered brick grid gives real rectangles and is cheaper than the eighteen
  hashes the cellular path spends.

* **The courses ran on the WORLD's axes.** Anchor's streets run diagonally, so
  the grid crossed them at an angle and the two arms of one crossroads looked
  like two different pavements. Reported as *"why is there such a mix of
  different types?"* -- and some of that mix is the world's own, since it
  interleaves `flag` and `cobble` tile by tile along one road, but this part
  was one pattern seen at two obliquities. The direction now comes from asking
  which way the paving CONTINUES, the same question the decking asks of its
  planks, so a street is laid along itself without this material knowing what a
  street is.

The joints were also set by eye at about half the width they needed, and were
under a pixel: a cobble is roughly ten pixels across at this camera. Measured
off a photograph.

### The fires were LED lamps

Reported from a photograph of a campfire: *"i don't think that really looks
like flames, it kind of looks like a LED lamp, the flames are not moving at all
or very faintly, maybe the cone is bigger than the flames underneath."* All
three observations were right and the last one names the cause.

A flame is a cone with `M_IntervalFlame` on it. The material feathers the
edges so the mesh's silhouette does not show -- except that it normalised the
radius against `Wide`, the half-extent of the whole INSTANCE, which is the
cone's radius at its BASE. A cone tapers. Two-thirds of the way up, every
pixel is inside a third of that radius, the feather (which starts at 0.30)
never touches it, and the top of the flame is a poster-paint wedge with the
mesh's own hard outline. Only the bottom inch was ever soft.

Normalised against the cone's radius AT THIS HEIGHT, the feather works from
base to tip and the flame never reaches the mesh's edge at all -- the cone
stops being a shape and becomes a region of space the fire is drawn inside.

And it did move; it moved the wrong thing. Opacity breathed between 0.72 and
SOLID, which is a lamp on a dimmer. The eye reads motion in a SILHOUETTE, and
that one was pinned to the mesh. Three tongues around the axis now push the
outline in and out, turning slowly at different rates, with a term in height so
a ripple travels from the fire to the tip rather than the whole thing pulsing
at once. Fire rises; anything that brightens and dims uniformly is a bulb.

Held under three-quarters opaque at the heart as well, so the brazier shows
through it.

Then it was a smudge instead, which is the other failure. Thinning the body
and softening the edge fixed the lamp and bought a pale amber wisp: at noon,
over lit grass, there was nothing there. The emissive had been pulled back in
an earlier session to stop it clipping to white -- correct while the shape was
nearly solid and nearly one colour, wrong once it had a real gradient and
feathered edges, because then the hot core is only a few pixels across and can
afford to be hot. Heart back up to 2.90, and thick down the middle while still
thin at the sides, which is not the same thing as thin everywhere.

THE PART THAT ACTUALLY FIXED IT WAS NOT SHADER WORK. Measured, nearly two
pixels in five changed between one frame and the next -- the flame was moving
the whole time. It still read as a lamp, because ONE CONE SEEN FROM ABOVE IS
ONE TRIANGLE however much its outline wobbles. Three tongues now, one tall in
the middle and two shorter leaning out, and the silhouette of three crossing
tongues is never a triangle twice running.

They gutter separately for nothing: `flame.hlsl` already takes each fire's
rhythm from WHERE IT STANDS, so three cones a few centimetres apart have three
phases without anything being passed in. The seed grid was a metre, which
rounded all three to one cell and made them beat in unison -- worse than a
single cone. Seven centimetres now.

AND THEN IT BURNED THROUGH THE HEARTH. Reported straight away: *"the cylinder
box it is in... the flame is burning through it."* The engine's cone is centred
on its own origin, so `oz=52` on a cone 138cm tall put the BASE of the flame
seventeen centimetres underground and its widest part exactly level with the
ring of stones -- out through the near rim and into the open. It had been
invisible while the cones were short and appeared the moment they were given
headroom to stand up in: two changes each right alone and wrong together.
`fire()` now reads `z` as the height the fire BURNS FROM, and every entry is
the top of the actual fuel -- the crossed logs, the ring, the platform, the
pot's stand -- read off the parts table rather than guessed.

### Three CC0 packs, and the thing measuring them said

KayKit was the obvious answer to the seventy-one props that are still engine
primitives, and it was turned down on sight: *"the kaykit pack doesn't seem to
fit well.. it's more for a smaller scale strategy game or something."* Correct.
Everything in this window is Quaternius, and a CC0 licence is necessary but
not sufficient -- the second test is whether it can stand beside a citizen
without looking borrowed.

So: Medieval Village Pack, Ultimate Modular Ruins, Farm Buildings. All three
CC0 1.0 Universal, declared in each pack's OWN `License.txt`. 124 meshes,
imported by `Tools/import_village.py`, and 24 words now drawn from them. The
list of props that are still primitives went from 71 to 55.

**THEY ARE NOT ALL AT THE SAME SCALE, and nothing says so.** Measured on
import, comparing the barrel each pack ships:

    Medieval Village   barrel  20cm tall     about half scale
    Ultimate Ruins     barrel 107cm tall     true scale
    Farm Buildings     Well 215cm, Windmill 972cm    true scale

Every scale in `parts.py` is therefore a measurement and not a guess, and
where two packs have the same object the true-scale one wins -- the well and
the fence come from the Farm pack, not the Village one. This is why
`import_village.py` measures every mesh and writes the sizes out: guessing a
number here is guessing whether a well comes up to a citizen's waist or their
chin.

### Assigning `parts` deletes what the helpers add

Three times in one afternoon, the same shape:

  * the firewood was set after `burn()` and the campfire came back as a bare
    pile of wood with no flame on it;
  * the new well mesh cleared `parts` after `fill()` and would have lost its
    water -- unnoticed, because a well is mostly a hole;
  * `stall` was claimed by `PROP_PROPS` as well, which runs later and won, so
    the market stand silently stayed a trestle.

The rule: anything that ASSIGNS `parts` has to run before every helper that
ADDS to them, and no word may have two tables that think they own it. The
comment about two tables owning a word was already in `parts.py`, about `stall`
specifically, and it happened again to the same word.

### A contact sheet that asks the right question

`gallery.py` grew a `built` mode. `folder()` photographs art off the disk,
which is right for a mesh with no row yet; `built()` photographs WORDS, drawn
at the scale the look asset gives them, which is the question three packs at
three scales actually raised. A citizen is stood in the grid first, at 1.81m,
because a sheet of props with nothing human in it is a sheet on which
everything looks plausible.

    RACK_ROLL=0 RACK_CELL=700 gallery.py built out.png well fence stall ...

RACK_CELL is new and not a nicety: the default 150cm was written for helms and
hatchets, and the first sheet of these packs came back as one solid pile of
overlapping buildings.

### A hearth is a hearth now, and one thread is still open

`hearth`, `campfire` and `watchfire` were a CYLINDER: ninety centimetres
across, half a metre tall, with two crossed CUBES on top for logs. That drum
is the "cylinder in the corner" and the "cylinder box the flame is burning
through" -- one object, reported twice, from two different rooms.

The drum came out of C++ as a default and nothing in `apply.py` had ever
overridden it, which is why it survived every pass over the fires. It is now a
bed of ash four centimetres deep, with a RING OF STONE round it and round logs
laid in the ring. The stones are `Pebble_Round_*` and `Pebble_Square_*` from
the CC0 Stylized Nature kit -- the same meshes the scree, shingle and gravel
are already scattered from, which nobody had thought to build a fireplace out
of -- laid by arithmetic off the index so that every hearth in the world is
recognisably the same hearth, varied the same way in every window.

VERIFIED IN THE DATA, NOT ON CAMERA, AND THAT DISTINCTION MATTERS HERE. The
row reads back correctly: seven stones in a ring at 44cm, three logs, three
flame tongues, a 4cm ash bed. On screen the stones cannot be made out, because
the fire washes out everything within about two metres of itself.

**That wash is unresolved and it is not what it looks like.** Eliminated by
measurement, each with the fire photographed before and after:

  * not BLOOM -- `r.BloomQuality 0` changes almost nothing;
  * not LUMEN indirect off the emissive -- `r.Lumen.DiffuseIndirect.Allow 0`
    changes almost nothing;
  * not VOLUMETRIC FOG -- `showflag.VolumetricFog 0` changes almost nothing;
  * not the flame's own emissive alone -- it persists in `showflag.Lighting 0`,
    but so would a light, so this one proves less than it seems.

By elimination it is the point light, still on at full strength with
`ForceDay` set to noon -- which the code at IntervalStructures.cpp:638 is
supposed to prevent and evidently does not. Two candidates, neither tested:
`Chosen` resolving to a different look object than the one `ForceDay` was
written to, or `E.bIndoors` being true for this campfire (it stands among
houses), which makes `Dark` 1 whatever the hour. Testing `bIndoors` is one log
line and should be the next thing anybody does here.

The intensities were cut to about a third on the way through -- a fire bright
enough to light a yard was bright enough to delete its own fireplace -- and
the lights were given a SOURCE RADIUS, because a fire is a ball of burning gas
about the size of the fire and not a mathematical point, and a point obeys the
inverse square all the way in. Both are improvements and neither was the
cause.

### `ForceDay` moves the sky and not the fires

Small, and it wasted a capture. `ForceDay` says it "changes nothing but
pixels", and it does change only pixels -- but it changes the SKY's pixels and
not the fires'. `bLightAtNightOnly` still consults the world's own hour, so
forcing noon over a world that is actually at midnight leaves every hearth,
forge and watchfire burning a 2400-intensity light under a noon sun, and the
ground around a campfire goes pure white. Judged like that, a perfectly good
fire looks catastrophically blown out. Either the flag should read the forced
hour too, or this file should carry the warning -- for now it carries the
warning.

### Every deed has a body now, and the world could not have told us

Forty-three motions covered a world with sixty-nine verbs. Cooking, smithing,
planting, fletching, brewing, buying and burying were all drawn as a person
standing perfectly still.

**It was not a missing table row.** The world admits exactly FIVE kinds of
`action` -- `gather`, `attack`, `attackp`, `walk`, `raise` -- and every other
deed resolves inside the interval it was asked for. Asked what a citizen is
doing on the tick they cooked a fish, the world answers `null`, and it is
right: the fish is cooked. There was no word to key on, so adding rows would
have changed nothing.

`UIntervalBridgeSubsystem::Doing` now remembers what our own hand filed and
holds it for a beat, hooked at `SendRaw` -- the one place every deed passes
through, so a verb wired next session is animated the day it is wired. 119
motions, grouped by what the BODY does rather than what the deed means, since
that is the only thing a viewer can see. Seen working: `wield` now stoops.

It is ours alone. Nothing arrives about anybody else's instant deeds and a
guess at one would be this window inventing world state.

### `raise` was a magic missile

`raise` is the world's word for BUILDING A MARKET STALL -- §6al, "raising a
stall is work, not a click", twenty intervals of standing in the open with your
goods on you. It was mapped to `Spell_Simple_Shoot`. A citizen putting up a
trestle table fired a spell at it for twenty seconds. It is `Push_Loop` now.

### Fishing was a man kneeling in the dirt with a spear

Asked about directly: *"and kneeling with a fishing rod? Isn't that weird?"*
It was weird, and it was not a rod. Two faults:

* `Fixing_Kneeling` is somebody on one knee working at the GROUND in front of
  them. It was chosen because "kneeling at the water's edge" sounds right
  written down; watched, the hands are busy at the dirt and nothing about it is
  aimed at the water. What fishing looks like from this camera is a figure
  standing still with a long thin thing out over the water.

* The tool was a `Spear`, which has a blade on it, chosen because the weapons
  kit has no rod. **But this project already had one** -- `parts.ROD`, a 170cm
  tapering pole with a cloth line off the tip, already hung on any citizen
  carrying the `rod` item. The motion had simply never been told about it. A
  thing the window could already draw was substituted for with a worse thing.


- **Fishing and cooking are done, and getting there took the whole island.**
  These were the last two of the original list and were called unreachable
  earlier in this file -- correctly, at the time: the only fisher's stall in
  the world is at Eastmere, every fishing spot is beside it, and both are east
  of the ridge. What made it reachable was three separate fixes, none of which
  were about fishing:
    * the NORTH PASS is open. The generator chokes only the south one, with
      forty-one boulders at a thousand strikes each and a signpost saying
      "the South Pass -- shut".
    * the map thought CRAGS WERE A WALL, so the whole east of the island was
      unroutable even after crossing.
    * and `go.sh` could not tell a refused step from a corner it could not see.
  The citizen walked from Anchor over the spine and down the east coast --
  something like three hundred and fifty tiles -- bought a rod for twenty of
  their twenty-two gold, and fished. Shorecraft went from nothing to 200.
  COOKING TOOK A THIRD FIRE. The two hearths nearest the water are both INSIDE
  buildings, walled on the side a citizen approaches from, and the window could
  route to neither. A campfire at a wayrest on the road is in the open, and
  that is where the fish were cooked -- three came out cooked and three came
  out BURNT, which is the world's skill check doing exactly its job at
  hearthcraft nothing.

- **Twenty-two minutes of a citizen's day went into a world that was never
  asked.** Every walk was refused, nothing moved, and `lastInput` had not
  advanced in thirteen hundred intervals -- which is precisely what an
  exhausted citizen, a blocked tile or a malformed deed all look like. The
  ninety-minute ceiling was checked against the ENGINE'S OWN arithmetic (the
  bins, `ceilBin`, `ceilStood`, `ceilingLeft`) and the bridge's copy agreed
  exactly: 2400 stood, 3000 left, not stood down. The crags were checked, the
  ridge predicate, the crossing rules, the mobs on the tile.
  There was no play session. `IsPIERunning` was false, so there was no hand to
  read the command file, and the remote had been writing "no hand yet" into its
  own log for every line. The world never heard any of it.
  `go.sh` pings the hand before it starts now and says so plainly. The guard
  reads only what its OWN ping answered -- the first version read the tail of
  the log and matched the stale "no hand yet" lines from the very session it
  was checking had been fixed, which is the same shape of mistake one layer up.
  THE LESSON: before asking why the world refused something, ask whether the
  world was told. A window that is not running is indistinguishable from a
  world that says no.

- **The island's spine was drawn as open country.** The ridge is the one great
  wall in the world -- two named passes cross it and the generator SHUTS one of
  them, with a signpost saying so -- and there was no way to look at the window
  and see where it was. Its tiles are ordinary `crags`, the same as the whole
  eastern third, so no terrain code could tell the spine from rough ground.
  The bridge tells the window now. The terrain chunk carried `tiles`, `road`
  and `hash`; it carries a `ridge` plane beside them, built from the
  generator's own `onRidge`, for the same reason the roads are told rather than
  derived -- a window that worked out its own ridge would disagree with the one
  beside it. The window is told WHERE it is and never what a ridge means.
  What grows there is a LEVEL's opinion, under a reserved key in the scatter
  table: `ridge` is not a terrain, so it has no row of its own and one is made
  by copying the shape of an existing row. IT MUST BE MADE BEFORE THE VARIANTS
  ARE CHOSEN -- copied from a grass row and left alone, the island's spine
  sprouted clover. Big rock in three sizes, nearly every tile and most of them
  several, and it is the one scatter in the window that CASTS A SHADOW: on flat
  ground a shadow is most of what makes stone read as high.
  Seen in the world from the east side, which needed the North Pass and the
  routing fix above to reach at all.

- **A third of the island was unreachable, and nothing in the world said so.**
  The map's impassable set was `sea, river, mountain, crags, cave`. The WORLD
  bars three things and the generator says so in eleven lines: water without a
  ford, the ridge without a road, the barrow without a road. `crags`,
  `mountain` and `cave` are ground NAMES, not walls -- the engine prices crags
  at 22 against the heartlands' 10, which is a cost, not a barrier -- and the
  east of the island IS crags. So every route into it came back "out of sight
  or walled in", and the whole eastern third might as well not have existed.
  Found by walking through the NORTH PASS, which is open: the generator chokes
  only the south one and plants a signpost reading "the South Pass -- shut".
  A citizen crossed the spine for the first time this session, stood on the far
  side, and could not route a single tile further. Two runs after the fix, the
  same citizen was ten tiles into the crags.
  THE RULE: ask the generator what it blocks. It exports `blockedAt`, and
  every guess this window has made about terrain has been wrong in the same
  direction -- too cautious, and silently.

- **A wounded PERSON showed nothing.** The ten-notch bar was given to beasts
  and never to citizens, so a fight between people was as blank as a fight used
  to be -- and §11d makes exactly that fight a thing the world expects, since a
  hauler carrying a consignment is the one citizen anybody may lawfully strike.
  Found by killing goblins at the pound: the goblin carried a bar and the
  citizen standing over it at 58 of 64 carried nothing.
  It rides on the NAME PLATE rather than in a second widget, because a person
  already has a plate and two of them over one head is a HUD. `TopHp` works as
  it does for a beast -- the world sends current hitpoints and never a maximum,
  so the window remembers the most it has seen somebody at, and a person met
  already wounded starts full and is honest from there. That is worth knowing
  when testing it: this citizen was first seen at 58 and correctly showed no
  bar until the next blow took them to 56.
  Seen in the world, notches under the name.

- **The goblin is green, and it was walked to.** `goblin_a` was chosen by NAME
  and is a blue creature holding a BASEBALL BAT -- photographed, exactly as it
  was reported from the stream. The kit ships four and they were all
  photographed this time before choosing: `goblin_b` has no textures at all and
  renders as grey blocks, `goblin_d` is the smallest, and `goblin_c` is green
  with pointed ears, a belt and a spiked club. The word draws `goblin_c` at
  0.2778, which is the same 1.3m the blue one was drawn at.
  Verified at the goblin pound itself -- the hedged pen on the Anchor-Oxenford
  road, ninety-eight tiles west of Anchor and the only place in the home
  country where you can look a goblin in the eye through a fence. Getting
  there meant walking round a tollgate, which is its own note below.
  THE LESSON THIS FILE KEEPS RE-LEARNING: a file called `goblin_a` is not a
  goblin until somebody has looked at it.

- **The guards at the pound wear their armour properly.** Worth writing down
  because restoring the keepers' kit made a great deal of gear visible for the
  first time, and gear at a fixed offset from a TILE rather than on a bone was
  the obvious thing to have broken. It has not: a guard stands with the helmet
  on their head and the cuirass on their body. The armour's scales look absurd
  in a dump -- a helmet at 12.5 and a cuirass at 21.2 -- and are correct: those
  meshes import about 1.6cm across and the numbers normalise them to a head and
  a chest. Read as a bug once during this session and they are not one.

- **Every level of detail in the world was chosen for a camera standing on the
  ground.** The ladder was `[1.0, 0.42, 0.16, 0.05]`, and screen size is the
  fraction of the VIEWPORT HEIGHT a mesh covers -- so LOD0 appeared only once a
  thing filled the whole screen, which nothing in a window that looks straight
  down ever does. The camera sits 1150 back and 1380 up, which is eighteen
  metres, and with a 58.7-degree vertical field of view that puts a 1.6m hedge
  at 0.133 and a 4.3m tree at 0.257: every hedge on the island drew at LOD3,
  108 triangles out of 899, and the tree beside it at LOD2. The ladder is now
  built from that arithmetic -- `[1.0, 0.10, 0.05, 0.02]`, LOD0 out to about
  twenty metres, which is the citizen's own surroundings.

  IT TOOK THREE ATTEMPTS AND EVERY ONE FAILED SILENTLY:
    * `set_lod_thresholds` over MCP wrote values that read back correctly and
      came back EMPTY after a restart.
    * `UStaticMesh` has no setter at all -- no `set_lod_screen_size`, and
      `auto_compute_lod_screen_size` is not on its property surface either, so
      both obvious routes answer "failed to find property".
    * `StaticMeshEditorSubsystem.set_lod_screen_sizes` is the real door, and
      even then the values reverted to the AUTHOR'S original ladder on the next
      restart -- because `EditorAssetLibrary.save_asset` defaults to
      `only_if_is_dirty=True`, and the subsystem changes the mesh without
      marking its package dirty. The save looked at a clean package and did
      nothing.
  A write that succeeds is still not a write that landed, and this file has now
  paid for that lesson in three different ways: a property that is not a
  property, a value the engine recomputes over, and a save that declines.
  The pass proves its own work now: it asks each mesh
  `is_lod_screen_size_auto_computed()` afterwards and names any that still are.

- **A hedge was a row of green boulders, and finding that out took far longer
  than it should have.** `hedge` drew `Bush_Common` at a uniform 0.85 -- a
  round shrub 1.6m across, stamped once per tile. From the side that is a bush;
  from THIS camera, which looks straight down, you see the top of a dense shrub
  where the leaf cards overlap completely and there is no silhouette to read,
  so a field boundary came out as a line of smooth green balls. They are now
  1.15 wide and 0.46 tall -- wider than the 200cm tile so neighbours MERGE into
  one clipped line, and about 73cm high so a citizen is the tallest thing in a
  field. `bAlignToRun` was already set and only starts reading as a hedge once
  the pieces actually touch.

  EVERY INDIRECT METHOD LIED, WHICH IS THE PART WORTH KEEPING:
    * the node list was silently truncated at 44 rows, hiding all fifty hedges
    * the asset's own render looks nothing like the same mesh from overhead,
      so "the thumbnail is leafy" proved nothing
    * `trace_world` finds only the ground, because instanced pools carry no
      collision
    * `r.ForceLOD 0` disproved a level-of-detail theory without suggesting
      another
    * and writing the whole `Props` map back to test a scale CORRUPTED it --
      round-tripping that JSON turns the four characters "None" into something
      the setter treats differently, which is the trap already recorded twice
      in this file. `apply.py` restored it.
  So `playremote.py` grew a `what <tileX> <tileY> [radius]`, which reads the
  renderer's own instanced pools and prints each instance's mesh and true world
  scale. It answered in one call what an evening of inference got wrong three
  times: at the goblin pound the fence is `Cube` at 2.00x0.26x1.0, the one
  round thing inside it is a `muck-heap`, and the nearest hedge is FIFTEEN
  TILES AWAY in Oxenford's fields. Nothing green was in the pen at all.
  It also grew `exec`, which runs a console command -- there is no cvar setter
  anywhere on the MCP surface, only a search, and without one a question like
  "is this a level of detail or a wrong mesh" cannot be asked at all.

- **It was never seventy-one verbs. It is EIGHTY-FOUR, and thirteen were still
  missing.** The note below records this window learning to file "all 71" of
  the world's verbs, and the number was believed for the rest of the session.
  It was measured with a regular expression over `INPUT_SCHEMAS` that only
  matched rows BEGINNING a line -- and several share a line with the row before
  them, `raise_market: {}, dismantle_market: {},`. That is the SAME mistake, in
  the SAME table, that cost twenty-one verbs the first time, and the note
  warning about it is four paragraphs further down this file.
  The authoritative test is the engine's own definition of a verb: a word with
  BOTH a `case` in validate() and a row in INPUT_SCHEMAS. By that test the
  world has eighty-four and this window could file seventy-one.
  WHAT WAS MISSING IS NOT MARGINAL. Two whole economies:
    * the market a citizen runs themselves -- `raise_market`, `stock_market`,
      `price_market`, `take_market`, `dismantle_market`
    * the trade between citizens -- `offer_trade`, `accept_trade`,
      `cancel_trade`
  and `build_brewpot`, `deposit_all`, `read_chart`, `recall`, `set_look`.
  All thirteen are wired and every one was checked AT THE DOOR, by printing the
  bytes the window sends. `offer_trade` is the only one that needed its own
  sender: four fields of three shapes, and an item that must travel as a real
  JSON null when coin is wanted, because the engine says plainly that
  "omission is not a representation" -- the same lesson the pickup's boolean
  taught. Its slots are sorted and de-duplicated into the canonical form, as
  `consign`'s are, so two windows asking the same thing sign the same bytes.
  THE LESSON, PAID FOR TWICE NOW: do not count this world's verbs by reading
  its schema table. Count the `case` labels in its validator.

- **"gave up after N runs at X,Y" was reporting the wrong place, and it sent
  this session chasing walls that were not there.** `go.sh` printed the
  position read at the TOP of its last iteration -- before that iteration's
  walk -- so a journey that was moving steadily the whole time reported the
  tile it had started from, and "gave up" read as "never moved". Several of
  the walls hunted tonight were journeys quietly making progress. It asks the
  world where it actually is now, and says "out of tries ... still short of"
  rather than "gave up", because those are different things.
  TWO REAL ROUTING FAULTS WERE UNDER IT, both fixed:
  A LEG THAT ENDS WHERE IT BEGAN. The route is computed from the ROUTE's first
  tile, which is not always the tile the citizen stands on, so the first
  straight run could name the citizen's own square -- filing a walk with no
  direction, which the world refuses ("a walk that goes nowhere is not a
  walk"), forever. The first leg that actually goes somewhere is taken now.
  AND A CORNER THE MAP CANNOT SEE. The map sees ten tiles and the world sees
  everything, so a route can aim through a keeper standing in a doorway or a
  beast that respawned onto the one diagonal every route wants. Re-routing
  produced the same route and the same refusal. When even a single tile is
  refused, the two tiles either side of it are tried; one of them almost always
  opens, and moving at all makes the next route a different route.

- **The Millbrook Bridge is tolled, and the toll is a PLANK.** Walking a
  citizen west out of Anchor, the near crossing turns out to have a tollgate at
  either end and a keeper beside it, and `pay` is refused however much gold is
  carried: the validator asks for `planks`, because "the keeper is mending the
  deck and a deck is made of sawn boards". Planks come from ONE sawpit, at the
  Sawyer's Camp in the Deepwood. This is the world working exactly as designed
  -- a crossing is an undertaking -- and it is worth writing down because
  nothing in the window says so and a citizen can stand at the gate with
  twenty-two gold wondering why the bar will not lift.

- **Every keeper in the world stood empty-handed, and the open item above had
  the reason backwards.** This file recorded a worry that a keeper's hat, staff
  or barrel might "hang off the body" at a fixed offset from the tile. The
  truth was worse and simpler: the kit was NOT DRAWN AT ALL. A brewer in Anchor
  was photographed with no barrel, and reading `keeper.brewer` back out of the
  look asset gave `parts: []`.
  TWO FAULTS, ONE ON TOP OF THE OTHER. The renderer's loop did
  `if (Kind->Skeletal) { StandFigure(...); continue; }` -- and that `continue`
  jumped the whole remainder of the loop, including the block that draws a
  kind's parts. So the moment keepers stopped being cylinders and became
  people, every tool in every town silently stopped being drawn. `apply.py` was
  then told to clear those parts, for the good reason that a hat and a cylinder
  would otherwise stand inside the person -- which made the data agree with the
  omission and hid it for good.
  Both are fixed. The renderer skips only the POOLED MESH for a standing
  figure and falls through to its parts; `apply.py` keeps the kit, because the
  hat was the only piece that needed moving and it is already moved thirty
  lines earlier, where anything above 190cm -- the top of the old cylinder --
  is sat back down onto a human crown.
  Seen in the world: the brewer has her barrel. It needed DAYLIGHT to judge,
  so the hour was forced to noon for one photograph and handed straight back.

- **Every fountain in the world was dry.** Found by walking to the one in
  Anchor and photographing it: a properly tiered plinth -- basin, column, upper
  bowl, finial, all in stone -- and not a drop of water in it. The water part
  existed and `fill()` was putting it in; it was simply INSIDE the stone. A
  part of scale `sz` stands centred at `oz`, so the basin (0.14 at z=46) fills
  z 39 to 53 and the water (0.03 at z=40) filled 38.5 to 41.5 -- buried in the
  middle of it, under a disc of stone that is wider than the water is. Lifted
  to z=55, just clear of the basin's top, and it now reads as a sheet of water
  around the central column.
  Checked the other six pools for the same arithmetic -- wellspring, dew-pond,
  bog-pool, birdbath, salt-pan and the well. The well's water is clear of its
  coping and the rest have no stonework of their own to be buried in, so the
  fountain was the only one.

- **Every fire in the world was a white paper cone.** A campfire in Anchor,
  photographed from four tiles away, was a cream-white shape in a ring of
  stones with no heat in it at all -- and the same blown-out white was in the
  very first screenshot of the session, at the lamps over Millbrook.
  The flame's colour ramp is right and reads correctly FROM THE SIDE: white at
  the heart, orange through the body, nearly out at the tip. But this window
  looks straight down. From overhead the heart fills the middle of the shape
  and the tip is a thin ring at the edge, so the end of the ramp a person
  actually sees is the hottest one -- and at 3.40 red and 2.30 green it clipped
  both channels at this window's pinned exposure (0.62) and arrived as white.
  The heart is pulled back to 1.90/0.92/0.26 and the body with it. It is still
  the hottest and brightest part of the fire and the ramp is untouched; the
  point of a heart is that it is hotter, not that it is blown out. Checked by
  eye at each step: white, then cream, then amber.
  THE GENERAL LESSON: a shading ramp built along an axis has a DIFFERENT
  reading from a camera that looks down that axis, and every fire, lamp and
  glow in this world is seen from above.

- **A refused run was filed twenty times over, unchanged.** A `walk` is a
  STRAIGHT run and the world takes it whole or not at all, so one tile anywhere
  along it that the map cannot see -- a beast standing in the road, a wall the
  frame did not carry that far -- refuses the whole leg. `go.sh` then
  recomputed the same route, filed the same run, and was refused again:
  "gave up after 20 runs" with a citizen who never moved, four times in one
  journey. The tell was always the same -- the FIRST step of the refused run
  is accepted on its own. It now takes one tile in that direction when a leg
  moves nobody, which is enough to make the next route a different route.

- **Nothing could tell a citizen where a river may be crossed.** The crossings
  are deliberately SCARCE AND NAMED -- five on the whole island -- and a river
  is two hundred tiles long, so a citizen standing on a bank had no way to
  learn whether the ford was eight tiles upstream or ninety downstream. The map
  sees about ten tiles and route-finding at that range cannot answer it.
  `Tools/ways.sh` asks the generator directly, the same way the map now asks
  about the ridge, and names every crossing with its bearing and distance --
  and the two rows at which the spine may be crossed. Found the hard way:
  a journey west from Tallyholm spent its whole time discovering, one refused
  leg at a time, that Watersmeet is called that because two rivers meet there.

- **The bestiary is COMPLETE, and an out-of-date note here said it was not.**
  All twenty-four beasts the world defines have art: the audit that said
  otherwise forgot `DRILL` (the training dummy and the archery butt, which are
  mobs rather than furniture) and `FACES` (the incursion, which is one
  silhouette in five skins under `incursion.<face>`). Anything auditing this
  again must union all six tables -- BEASTS, WILD_BEASTS, WILD_STILL,
  DARK_BEASTS, DRILL and FACES -- or it will invent a gap and go shopping for
  art the project already has.

- **There is now a reader for both art formats, and both are checked against
  the scales already in the project.** `Tools/fbxsize.py` and
  `Tools/glbsize.py` measure a model from ITS OWN FILE, which is the third time
  this project has needed that and the first time it is written down as a tool.
  A skeletal mesh's `get_bounds` reports the ANIMATED extent -- `goblin_a` comes
  back at 462 metres because a clip walks its root -- and every scale derived
  from it is wrong by that factor.
  THEY ARE VALIDATED, not merely written: the glTF reader reproduces every
  measurement already recorded here, exactly. goblin_a 4.63m, ogre 5.60 ×
  0.5085 = 2.85m, wolf 5.55 × 0.2341 = 1.30m, goat 5.92 × 0.2027 = 1.20m,
  bear_a 2.47m. And `goat.glb` measures identically to `Sheep.fbx` -- the kit
  builds both off one body -- which cross-checks the FBX reader against the
  glTF one on the same creature.
  A glTF is the kinder format: every POSITION accessor carries its own min and
  max, so the extent is READ. An FBX hides it -- the vertices are a shape, not
  a size, and the Model node's `Lcl Scaling` (65 to 100 in this kit) is what
  turns one into the other.

- **The map could not see the island's spine, and it stranded a citizen.**
  Sixty routing runs died at the South Pass, every one a refused step into the
  same five columns of rock, with nothing anywhere saying there was a mountain
  there. The ridge is not a TERRAIN CODE -- it is a predicate, `onRidge` in the
  world generator -- so the terrain chunk returns those tiles as ordinary
  `downs` and the map called them open country.
  Found by decoding the terrain chunk by hand (the codes are an index into the
  bridge's own `TILE_NAMES`: 24 is `downs`, 7 is `chalk`), seeing that the
  ground was perfectly walkable, and then asking the generator directly. The
  map now consults `onRidge` and draws it as rock, softly imported so a window
  onto some other world simply loses the ridge rather than falling over.
  A SECOND THING WAS TANGLED IN IT, and it is worth separating: a killed mob is
  still listed and still stands on its tile, and it RESPAWNS. Two scree-imps
  died, the way north looked clear, and by the time the route was recomputed
  they were back and holding the one diagonal every route wanted. `around.sh`
  now prints each mob's hp, and `DEAD` for a corpse, because seven arrows went
  into a body that was already dead and every one was correctly refused.

- **Fishing and cooking are not reachable from the west of the ridge, and that
  is the world, not the window.** The only fisher's stall in the world stands
  at Eastmere and every fishing spot is beside it, both east of the spine; the
  only raw food the world has is `raw-fish`, `deep-fish` and `eel`, so there is
  no cooking without fishing first. The South Pass is the near crossing and it
  is choked with forty-one rockfalls at a THOUSAND strikes each -- eleven days
  of communal digging, and "the only thing citizens can do to this island that
  the next founding will not undo". A citizen with forty minutes does not open
  it. The North Pass is a hundred and fifty rows away.

- **A citizen who wielded a tool was shown wearing nothing, and drew nothing
  in their hand.** Found by wielding an iron-hatchet and reading the panel:
  the whole WORN block sat at the empty placeholder while the world's own record said
  `equipment.weapon = {"item":"iron-hatchet","qty":1}`.
  An equipment slot holds a STACK, the same shape as an inventory slot, and
  both readers wanted a bare name. The panel asked `TryGetStringField` on an
  object, which fails; the body asked the entity flattener for
  `equipment.weapon`, and the flattener descended exactly ONE level, so it
  handed back the condensed JSON of the stack as if it were an item name --
  which matches no kit in the wardrobe. Two silent failures from one wrong
  assumption about the shape.
  The flattener now descends to a bounded depth, so `equipment.weapon.item`
  exists alongside the stack, and both readers ask for the name.

- **The window's own gate could not be opened by anything but a person.**
  `AIntervalGate` holds the title card up until somebody crosses it -- which
  is deliberate, the world is entered rather than arrived in -- but the PIE
  viewport's UMG is not in the editor's Slate tree, so the button cannot be
  clicked from outside and every editor restart came back stranded on the
  title screen. `Enter` was already BlueprintCallable for this reason and
  nothing called it. `gate` is now a word the remote understands. It is NOT in
  the verb table: that table is the WORLD's vocabulary, and this word is the
  window's -- nothing is filed, nothing is signed.

- **Every leaf in the world was a black tile with a leaf painted on it.**
  Canopies read as heaps of dark shattered glass, which is what "improve the
  trees" was really pointing at. The foliage sheets are ATLASES of leaf
  clusters, three-quarters transparent, and the alpha channel is the only
  record of where a leaf ends -- and the shader never read it. The opacity
  mask was `(Skin.z >= Cut) ? 1 : 0`, a test written for a CITIZEN'S COLLAR,
  and every foliage instance sets `Cut` to -100000 so the collar test always
  passes. So the mask came out 1 for every pixel: each leaf card rendered as a
  full opaque quad, a little green leaf in a wide black tile.
  The trunk of the same tree looked perfectly well throughout, which is what
  made it read as a modelling fault rather than a material one -- bark is
  solid geometry and has nothing to cut.
  Ruled out first, by measurement rather than by argument: the wind (the
  canopy is just as shattered with `Sway` at zero), two-sidedness (already
  on), the blend mode (already `BLEND_Masked`), and the wrong-texture fault
  that bit the bushes (the mesh has the right sheet on the right slot).
  The sheet's alpha now reaches the shader on its own lane, gated by `Cover`
  so that a person -- whose sheet is opaque and whose only cut is the collar
  -- is untouched.

- **A deed could vanish between the window and the world.** Twice a `buy`
  filed from Unreal changed nothing: gold unmoved, `lastInput` unmoved, no
  refusal in the feed -- while the identical deed typed straight into the
  bridge door succeeded seconds later. The window looked guilty and was not.
  `act()` only sent upstream `if (up?.readyState === 1)` and returned `ok`
  REGARDLESS, so a deed filed while the pillar socket was reconnecting was
  dropped and reported as accepted. That is the one failure this bridge exists
  to prevent: a refusal with no reason and no trace.
  Proved by printing the bytes at the door. The window's buy arrives as
  `{"type":"buy","item":"iron-hatchet"}` -- character for character what the
  hand-typed injection sends -- so the two paths were never different, and the
  difference was only ever WHEN. A dropped deed now comes back as "the pillar
  is not listening".

- **The window could file 26 of the world's verbs. It went to 71 here, and
  to all 84 later -- see the entry at the top of this list.**
  The rest were never refused by the world -- they were never SENT, which is
  worse, because nothing said why. They are generated from the engine's own
  INPUT_SCHEMAS, name for name and type for type, rather than typed out from
  reading.
  TWO LESSONS PAID FOR ALONG THE WAY. The first sweep read the schema table
  with a regular expression that only matched entries written on one line, so
  twenty-one multi-line ones came back looking like verbs that take no
  arguments -- and a verb wired with the WRONG fields is worse than a missing
  one, because it is filed, refused, and reads as a rule of the world. `swear`
  was the worst of them: its schema validates the calling with a function
  rather than a type, so it generated a swearing that could never be accepted.
  The authoritative test is whether the engine has a validator `case` for a
  word; the schema table alone is not enough.

- **A fight showed nothing.** Two figures stood next to each other and one
  eventually fell over; whether a blow landed or the thing was nearly dead was
  only in the socket. A hurt creature now carries a ten-notch bar that runs
  green to red. Shown ONLY on something that has been wounded -- a plate over
  every sheep on the island would be a HUD, and this is a window.
  The world sends current hp and never a maximum, so the window remembers the
  most it has seen a creature at; a beast is nearly always met whole, and one
  met already wounded simply starts full and is honest from there.
  STILL TO BE JUDGED BY EYE on a long fight: a goblin has 5 hp and dies in
  three strikes, which is not long enough to read a bar.
- **`fight.sh` could not close through a fence.** It walked straight at its
  target, so twenty runs went into the same refused step at the goblin pen.
  Closing is handed to `go.sh` now, which reads terrain and walls; verified by
  killing a goblin across the pen fence -- "arrived 357,259 in 1 runs" and then
  straight into striking.

- **Loot was invisible.** `Frame.Ground` arrived every interval and nothing
  drew it, so a drop fell, lay for its hundred intervals and expired with no
  way to know it was ever there -- the one thing a citizen looks for after a
  fight. Now drawn from the item's own art where it has some and a plain bundle
  where it has not, scattered within the tile by the drop's own id, and drawn
  low and centred because the world refuses a pickup unless you are standing ON
  it. The digest had to learn about loot too, or a drop would have appeared
  only when somebody happened to fell a tree nearby.
- **The bridge made every birth wait seventeen minutes** for a door the world
  opens after five. `VIGIL_TICKS` is 300 and says "FIVE, NOT TEN, AND NOT
  SEVENTEEN"; the bridge held a hand copy of 1000 from when an interval was
  600ms. It reads `vigilTicks` out of the `hello` tables now. Third hand-copy
  bug of the session, after the stall goods and the blocking-node list.
- **Fourteen keeper trades shared two outfits**, and every citizen in the world
  drew from the same two. The paid tier of the same CC0 kit adds a wizard, a
  noble and two knights on the SAME skeleton, so they joined the animation
  library exactly as the first four did. Oberon has a robe; the banker dresses
  like money; citizens draw from eight.

- **Every tree wore its own placeholder.** These words were a CONE ON A
  CYLINDER before there was tree art: the cone was the kind's `mesh`, the
  cylinder a `part` beneath it. Real meshes replaced the cone and said nothing
  about the cylinder, so every tree in the world stood beside a bare timber
  post. Reported from the stream as "the tree seems to have two trunks".
- **Every keeper stood beside their own discarded body.** Same shape of fault,
  found the same way. Giving keepers a human figure cleared `mesh` with a JSON
  null, and this asset wants the four characters "None" -- a note the Mobs
  table already carried. Handed a null it kept the cylinder.
- **The bushes were wearing the colour chart.** An override sent `Bush_Common`
  to the `Leaves1` sheet to stop it being autumn-red; that sheet's texture is
  the kit's 1024 PALETTE, 78% transparent. Their UVs were cut for a real leaf
  sheet, so they landed in the grey void and picked up stray swatches.
- **The camera followed the tile, not the citizen.** `Heart()` returned
  `TileToWorld(Me.X, Me.Y)`, which moves 200cm once a second, and the camera
  eased toward it -- lurching and settling every tick beside a body that was
  gliding. It follows `LastDrawnAt` now.
- **The stride finished early and waited.** The interpolation divided by an
  average of past intervals; arrivals scatter 744-1032ms and an average is
  short of half of them. Leaning the span 14% long costs nothing, because an
  unfinished stride is redirected from where it reached, while a fast one is a
  visible stop.
- **Citizens walked sideways.** The figures front along Y -- measured from
  their own bounds, Male_Ranger is 180cm across X and 37 across Y, a T-pose --
  while Unreal takes +X as forward. The heading was always right; the body was
  mounted ninety degrees to it.
- **Rivers sounded like the sea.** `sand` was mapped to the sea bed, and a
  beach and a riverbank are the same word. Banks now take the sound of what
  they border.
- **Water was a flat blue tile**, bridges were flat brown ones, and sand had no
  grain. All three are now drawn: depth from how much of the neighbourhood is
  also water, boards laid across a span, ripples and grain on sand.
- **Every ground grew exactly one plant.** A meadow was tens of thousands of
  one tuft. Each ground now names what else it grows, and the foliage master
  varies hue and value per instance.

- **`pickup` never worked at all.** `confirm` was sent through the integer map
  and arrived as `1` where the world's normalizer demands a boolean, so every
  pickup was refused. Fixed with `SendIntentBool`; verified by killing a goblin
  and taking its bones.
- **Fence panels faced one way.** Yaw was jitter-or-zero and never consulted
  the run, so a rectangular pen had two solid sides and two with visible gaps.
  Panels now take their facing from orthogonal neighbours of the same word, via
  the data flag `bAlignToRun`.
- **Goblins drew as green cylinders** although `goblin → goblin_a` was already
  in `WILD_BEASTS`. The look was right; the **level actor** was holding a stale
  copy, so the editor must be restarted *before* `apply.py` -- the same trap
  that ate the roofs. `apply.py` now names any beast with art but no `Mobs` row.
- **Every short walk reported itself blocked** and abandoned the remainder,
  while the tile it refused was walkable. Two causes at once: a deed takes 2–3
  intervals to be signed, carried and applied but the hand judged after one;
  and a one-tile walk finishes *inside* an interval, so `action` never reads
  `"walk"` for it. Now judged on `lastInput` moving.
- **Refused deeds were silent.** The world says nothing when it declines
  something. The hand now waits `AnswerPatience` intervals for `lastInput` to
  move and otherwise says "the world would not take that".
- **Closing time was invisible.** A stood-down citizen is indistinguishable
  from a broken bridge. The panel now shows the remaining allowance, the
  world's own warn band, and being stood down.
- **Hauling was invisible.** Taking a consignment empties the pack into a
  container the window could not see, which reads as having lost the goods.
  The panel shows `hauling N -> town` and the load is drawn on the back.
- **`attackp` could not be filed**, so a citizen could never be struck -- the
  half of combat §11d is built on.
- **The map knew nothing of terrain**, so a river read as open meadow and every
  route through it came back blocked from a tile the map had just called
  walkable. It now reads the bridge's terrain chunks.
- **The map treated `plot` as a wall.** The engine documents making exactly
  this mistake: 1,269 of the island's 1,370 field plots were unreachable. Now
  uses the world's own rule -- everything bars a tile except
  `smokerack, brewpot, watchfire, fire, market, cart, dedication, span, plot`.
- **`MaxSteps` was 24** against the world's 512, and the leg logic gives up
  after three runs -- so no click could reach past 72 tiles and a journey needed
  an outside loop. Each extra deed also spends an interval of the daily
  allowance. Now matched to the world; one deed has since carried a citizen 59
  tiles.
- **A newborn reported no allowance at all**, because a citizen minted minutes
  ago has no ledger yet. No ledger means nothing spent, which is an answer.
