# What to do next

A standing list, so that running out of an obvious next step never means
stopping. Ordered by how much of the world it opens up, not by how easy it is.
Struck through in `FOUND-BY-PLAYING.md` as each is seen working.

The rule this file exists to serve: **the window's job is total coverage.**
Every word the world uses must be drawn properly, and everything a citizen can
DO must be wired. Anything below that is a placeholder is a task, not a
decision.

---

## 0. THE FIFTY-NINE PROPS THAT ARE STILL ENGINE PRIMITIVES

The standing instruction, in the user's words: *"We have to make sure every
single node type and kind in the world is drawn properly."*

`Tools/audit.py` answers the first half. It had been dying on
`KeyError: 'weapons'` for some time -- it read a snapshot of a running node
and `Tools/scope.mjs` had replaced that with the engine's own export -- and
now runs:

    weapons  37/37   armour 13/13   mobs 24/24
    node types 66/66   keepers 23/23   stalls 7/7

Every WORD the world uses has a row, and the window's own log agrees: a grep
of `no mesh for it` comes back empty.

**THIS COUNT IS MUCH SMALLER THAN IT WAS.** The audit's second half now says
**10 of 200 prop rows are still an engine primitive**, with 23 more that are
primitives on purpose. It said 71 of 186 when this file was written. The ten:

    landmark.barricade   landmark.bridge-stone   landmark.chopping-block
    landmark.ladder      landmark.log-pile       landmark.scaffold
    landmark.sentinel    landmark.standing-stone landmark.stump
    landmark.withy-stack

And three of those ten -- chopping-block, stump, withy-stack -- have composed
parts on them already and read correctly in a photograph; they are counted
because their BASE mesh is a primitive, which is a measure of how they are
built and not of how they look. The standing stones and the sentinel
photograph as menhirs and are arguably finished too. Judge them from a
capture before touching them. Twelve of those were closed by pointing the keepers
at CC0 meshes this project already owns, which is the pattern for most of the
rest: Quaternius' Fantasy Props MegaKit is imported, at real scale, and
`/Game/Interval/Props` holds ninety-odd meshes nobody has wired.

Work it in this order, hardest-to-miss first:

1. **The forty `landmark.*` kinds.** Over half the backlog by count. Skep,
   scarecrow, haystack, milestone, way-post, gibbet, mill, shipwreck,
   siege-engine, drowned-bell, upturned-boat, peat-stack, turf-stack... Some
   have a mesh waiting (`Dummy` is a scarecrow, `Crate_Wooden` a turf-stack,
   `Chain_Coil` and `Rope_1` most of a gibbet); most do not and want a pass
   through the CC0 kits.
2. **The things a citizen stands next to every day**: `well`, `signpost`,
   `fountain`, `tollgate`, `muck-heap`, `ossuary`, `looking-glass`, `railing`,
   `fence`, `ferry`, `bellwork`, `gibbet-shoal`, `dedication`, `landmark`.
3. **The fires** -- `campfire`, `hearth`, `watchfire`, `furnace`. Their flames
   are now three tongues and read as fire; the FUEL under them is still two
   crossed cubes.
4. **What is honestly a box and can stay one**: `wall`, `wall.*`, `rampart`.
   A wall is a scaled cube, the timber-frame material does the telling, and
   these should be struck off the list rather than "fixed".

The audit prints the whole list; run it rather than working from this summary,
because it is the thing that cannot go stale.

## ~~1. The ridge should look like a mountain ridge~~

DONE, and half of it was already done when this was written. The bridge had
been sending the `ridge` plane beside the road one for a while, the window was
decoding it (as `Chunk.Spine`), and `SpineScatter` was already planting big
rock along the crest. What was missing was the other word in this item's own
brief: RISING.

The spine was flat. 1826 tiles running north to south, x 610 to 635, drawn as
a line of boulders lying on level ground, and from above you could not see
that there was a wall there at all. Nothing in the elevation field knows about
it either: `elevAt` is two octaves of noise and the ridge is not one of them.

So `HeightOfTile` lifts the ground on spine tiles, by `SpineRise` on the look
(the level says how high; the window only knows where it was told). The hard
five-tile band is blurred over four tiles into a rounded rise, and a road takes
its own lift away BEFORE that blur, so the one crossing comes out as a saddle
with rock standing either side rather than a road over a wall.

The height was measured by looking, three times: eight metres is a bank at the
edge of a field, twenty over a two-tile blur is a wall of grass like the face
of a dam, and sixteen over four tiles is a slope a person could walk up to a
crest lined with boulders.

## 2. Walk the whole island and photograph every region

Nine regions and the window has been seen in perhaps four. The Fens, the Moor,
the Deepwood, the Crags proper, the isles, Eastmere and the southern shore have
never been looked at. Every region visited so far has produced at least one
defect that nothing else would have found -- the foliage mask, the flame, the
fountain, the keepers' kit. This is the highest-yield thing on the list.

## 3. The metal ladder

DONE: `fish` and `cook`, which were the last of the original list -- a citizen
walked from Anchor over the North Pass and down the east coast, bought a rod at
Eastmere and fished, and cooked the catch at a wayrest campfire.

STILL TO DO: `smelt` and `smith`, at the furnace and the anvil. Ore into metal
and metal into a shape, two trades two hundred and thirty-eight tiles apart,
and the window has touched neither.

## 4. The trades nobody has practised

Measured against the engine's own skill list, the window has seen woodcraft,
earthcraft, sorcery, marksmanship, prowess and hearthcraft move. Untouched:
**shorecraft** (fishing), **mourning**, **wayfaring**. Each is a different part
of the world and each will exercise words the window has never drawn.

## 5. The market and the trade between citizens

Thirteen verbs were wired late and eleven of them have never been FILED in
anger -- the whole of `raise_market`, `stock_market`, `price_market`,
`take_market`, `dismantle_market`, and `offer_trade`/`accept_trade`/
`cancel_trade`. A citizen running their own stall is a part of the world the
window has never seen at all.

## 6. Judge the wound bar on something that lives

A goblin has five hitpoints and dies in three strikes, which is not long enough
to read a bar. Something with real hitpoints -- a troll, a skeleton-knight, the
gibbet-king -- would say whether the ten notches read at this camera's
distance.

## 7. The horse

The user's call, and they are leaning towards dropping it. The world has no
mount and the constitution names the trade RUNNER deliberately, because §11d's
risk is the point of it. The art exists. Left here so it is not forgotten.

---

## How to work down this list

- **Walk, do not reason.** Every wrong answer this project has produced came
  from inferring instead of looking. `Tools/what.sh`-style queries
  (`what <tileX> <tileY>`), `soil.sh`, `ways.sh` and a photograph settle things
  that an afternoon of argument does not.
- **Ask the generator.** It exports `blockedAt`, `onRidge`, `passesOf`,
  `bridgesOf`. Every guess this window has made about terrain has been wrong in
  the same direction: too cautious, and silently.
- **Rotate at the warn band.** Ninety minutes a citizen; mint a fresh key and
  carry on rather than stopping.
- **Hand the hour back.** `ForceDay` and `ForceRain` return to -1 before
  finishing, every time.
