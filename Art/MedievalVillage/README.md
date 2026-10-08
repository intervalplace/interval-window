# Quaternius -- Medieval Village Pack (Dec 2020)

Author: Quaternius (https://quaternius.com, https://www.patreon.com/quaternius)
Pack page: https://quaternius.com/packs/medievalvillage.html
Licence: **CC0 1.0 Universal**, declared in this folder's own `License.txt`
(read from the file, not inferred from an aggregator's metadata -- see the
note in `Art/RPGCharacters/LICENCE.txt` for why that distinction is kept).

Fetched from the author's own Google Drive mirror, the same route
`Art/Quaternius/README.md` records for the character kit.

WHY THIS PACK AND NOT KAYKIT. KayKit is CC0 and good, and it was turned down
on sight: its proportions are stylised toward a small-scale strategy look and
beside a Quaternius citizen it reads as a different game. Everything already
in this window is Quaternius, so staying inside that catalogue makes scale and
style a guarantee rather than a judgement.

What it closes, against `Tools/audit.py`'s list of props that are still engine
primitives:

| model | the word it draws |
|---|---|
| Well | `well` |
| Fence | `fence`, `railing` |
| Hay | `landmark.haystack` |
| Cart | `cart`, `broken-cart` |
| MarketStand_1 / _2 | `stall` and its seven trades |
| Mill | `landmark.mill` |
| Bell, Bell_Tower | `bellwork` |
| Gazebo | `landmark.gazebo-post` |
| Bonfire, Bonfire_Lit | `campfire`, `hearth`, `watchfire` |
| Crate, Barrel, Bag, Cauldron | keeper kit, stall goods |
| Path_Square, Path_Straight, Stairs | paving details |
| Rock_1..3, Door_*, Window_* | walls and landmarks |

Buildings (Blacksmith, Inn, Sawmill, Stable, House_1..4, Mill) are here but
are NOT the reason the pack was fetched: this window builds its houses
procedurally from the world's own wall and roof data, and a prebuilt house
cannot sit on a footprint the generator chose.
