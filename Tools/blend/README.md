# Authoring the art, headlessly

`Tools/forge.py` writes OBJ from six primitives: a quad, a triangle, a lathe, a
plate, a tube and a blob. It has made eighty meshes and it is the reason this
world has a fishing rod, a handgonne, four masks and forty-nine goods that no
CC0 kit had. It also has three hard limits, and all three showed up the day a
bird was needed:

  NO UVs AT ALL. The OBJ carries `v` and `f` and nothing else, which is fine
  for flat-coloured art and is why the importer threw
  `UVs.IsValidIndex(VertexData.UVIndex)` on the bird.

  NO SMOOTHING, NO BEVEL, NO SUBDIVISION. Everything is faceted at whatever
  resolution the loop that made it chose, so an organic shape is either coarse
  or enormous.

  NO MIRROR AND NO BOOLEAN, so a symmetrical thing is written twice by hand
  and a hole is not possible at all.

So anything organic is authored here instead, in Blender, run HEADLESS from a
script that lives in this repository:

    blender --background --python Tools/blend/fowl.py

which is the whole point. Nothing about this is a person opening a modeller and
remembering what they clicked: the script is the asset, the asset is rebuilt by
running it, and the repository holds both. That is the same property every
other thing in this project has -- the sounds are synthesised, the icons are
rendered, the materials are built from HLSL, the island is generated -- and it
is the property that would have been lost by modelling by hand.

WHAT STAYS IN `forge.py`. Hard-surface things whose shape is a few numbers: a
plate, a pole, a box, a heap. It is faster to write and faster to read, and a
barrel does not need a subdivision surface.

WHAT COMES HERE. Anything with an organic silhouette, anything that needs UVs,
anything that needs a rig, and anything symmetrical enough that writing it
twice would be silly.

CONVENTIONS, so these agree with the rest of the world:

  CENTIMETRES, AND MEASURED. A citizen is 181 cm. Every scale mistake in this
  project came from not measuring, so each script prints the size of what it
  made and the number is checked against the real animal or object.

  +X IS FORWARD, +Z IS UP, and a held thing runs along +Z from a grip at the
  origin -- the convention the whole Quaternius kit uses and that
  `parts.GRIP_WEAPON` is derived against.

  MATERIAL NAMES COME FROM `forge.PALETTE`, because `dress_forged.py` makes one
  material instance per palette key and binds mesh slots by name. A slot named
  anything else arrives in Unreal as grey.

  WRITTEN TO `Art/Forged`, beside everything `make_art.py` writes, so
  `import_forged.py` and `dress_forged.py` pick them up with no new wiring.
