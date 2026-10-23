# Rendered here, not downloaded

The inventory sprites, photographed from the meshes this project already has:
see `Tools/icons.py`. Most of the world's items are already a real mesh
somewhere, because somebody is wearing or wielding one, so a sword's icon is
the same sword that is on the citizen's back rather than a drawing of one.

No third-party licence applies to the rendering. The meshes they are rendered
from carry their own, recorded in the folder each came from.

## The handbook no longer prints these

From 24 October 2026 the printed handbook draws its items and its bestiary
from the browser window's own canvas paths instead, by way of
`interval-bridge/sprite-svg.mjs`, which replays those paths as SVG. Three
reasons, and the first decided it:

- These are photographs of third-party CC0 meshes, so the book's look was
  assembled out of several people's kits and no two agree about scale, light
  or how shiny iron is. The window's drawings were all authored here.
- A photographed mesh is at whatever angle the icon camera held it, and at
  7.6mm an axe seen nearly end-on is a brown smudge.
- The paths carry no bitmap, so the press gets the press's resolution rather
  than 128 pixels stretched over 7.6mm. The whole world's art is 59KB of
  vector against 20MB of PNG.

They are still rendered, still used by anything that wants a photograph, and
still the fallback for any word the window has no drawing for. There is
currently no such word. `Art/Icons-rendered-backup-2026-10-23` is a copy of
the set as it stood on the day this changed.
