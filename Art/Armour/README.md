# Armour -- CC0, from OpenGameArt

The character kits in use carry no helm and no breastplate in their free tiers,
so the head slot had no art at all. These three are CC0, each declared on its
own page at opengameart.org (the licence was read from the page, not inferred
from a search filter):

| file | source | licence as stated |
|---|---|---|
| Helmet.obj | opengameart.org/content/low-poly-medieval-helmet | CC0 |
| Bucket Helmet.fbx | opengameart.org/content/bucket-helmet | CC0 |
| Iron_Crown.obj | opengameart.org/content/iron-crown | CC0 |

A helm and a crown are RIGID props: they hang on the `Head` bone the way a
sword hangs on `hand_r`, so they need no rig and no skeleton of their own.

## The knight, and the breastplate cut out of him

| file | source | licence as stated |
|---|---|---|
| Knight_Helmet1.obj | quaternius.itch.io/lowpoly-animated-knight | CC0 |
| Knight_Helmet2.obj | same pack | CC0 |
| Knight_Helmet3.obj | same pack | CC0 |
| Knight_ShoulderPads.obj | same pack | CC0 |
| Cuirass.obj | cut from `KnightCharacter.obj` in the same pack | CC0 |

Five of the world's thirteen armour words are `*-plate` and no CC0 pack in use
ships a breastplate -- the free tiers carry helms and nothing for the body.
Quaternius's CC0 Knight does, but his whole suit is ONE material group called
`Armor` running from the greaves to the gorget.

`Tools/slice_obj.py` cuts it. A `.obj` is a text file of vertices and faces, so
taking the faces that use one material, and of those the ones lying between two
heights, is arithmetic and not a modelling job -- the same trade `sheet.py`
makes for PNGs, and for the same reason: nothing has to be installed.

The cut is `Armor`, y 2.45 to 4.05 out of a figure 5.58 tall, which is waist to
gorget. It is not closed at the waist or the arm holes and does not need to be:
it is worn over a body, and the body is what you would see through them.

Licences on both packs were read from their own pages, not inferred from a
search filter. Two OpenGameArt breastplates were looked at first and rejected
-- "Fantasy Breastplate" is CC-BY-SA 3.0 and "Leather Breastplate" is CC-BY
3.0, and one pack that the site's own CC0 filter returned says CC-BY 4.0 on the
page itself. The filter is not the licence.
