#!/usr/bin/env python3
"""Make a mesh from anywhere look like it belongs here, in Blender.

WHAT THIS IS FOR. The back half of this project's art pipeline is settled and
proven: an OBJ in Art/Forged whose material groups are named from
`forge.PALETTE`, in centimetres, Z up, goes through import_forged.py,
dress_forged.py, apply.py and icons.sh without anything knowing where it came
from. What there is no front half for is a mesh that did NOT come out of
Tools/forge.py -- anything fetched, anything generated, anything modelled.

Such a mesh arrives wrong in four ways at once and they are all mechanical:
it is dense, it is textured, it is at whatever scale its author used, and it
is oriented however their tool writes. None of that is a judgement; it is
arithmetic, and arithmetic belongs in a script rather than in somebody's hands
in a GUI, for the same reason every other step here is scripted.

THE COLOUR IS THE WHOLE ARGUMENT, AND THERE ARE TWO RIGHT ANSWERS TO IT.

This world looks the way it does because everything is flat colour on
M_IntervalFlat, with Rough, Course and Grain doing the surface. A textured
mesh dropped in beside that reads as pasted on however good it is. So the
texture is always SAMPLED and then THROWN AWAY. What happens to the colour
afterwards depends on what the thing IS.

  --palette (default)  for PROPS. Each material is matched to the nearest
                       entry in `forge.PALETTE` and the group renamed to it,
                       after which dress_forged.py paints it exactly as it
                       paints a forged piece, because as far as it can tell
                       that is what it is.

  --keep               for CREATURES. The artist's own colour is kept and
                       written to a sidecar, and dress_normalised.py builds one
                       M_IntervalFlat instance per slot from it.

USE --keep FOR ANYTHING ALIVE, and the reason is measurable rather than a
matter of taste. `forge.PALETTE` is a palette for this world's AUTHORED PROPS
-- bone, iron, oak, thatch, ale, fish -- and it contains exactly ONE real
green. Put a goblin through it and its main hide, a perfectly ordinary
(0.137, 0.192, 0.030), comes out as `Sulphur`, a yellow, because the nearest
green is a long way off and a yellow is nearer. A yellow goblin is not a
coherent goblin.

That is also what this project already does: dress_wild.py reads each
creature's own colour out of its glTF and puts it on M_IntervalFlat unchanged.
The master material is what makes a creature belong here, not the palette.

    blender --background --python Tools/normalise.py -- \\
        <in.glb|in.obj|in.fbx> <word> <tall-in-cm> [--budget 1200] [--keep-pose]

It writes Art/Forged/<word>.obj. Then:

    Tools/pyrun.sh import_forged.py
    python3 Tools/dress_forged.py
    python3 Tools/apply.py

PROVENANCE IS NOT THIS SCRIPT'S BUSINESS AND IT WILL NOT PRETEND OTHERWISE.
It will normalise anything it is handed. Whether a given mesh may be used here
at all is the standing rule in CLAUDE.md -- third-party art is CC0 and the
licence is read from the asset's own page -- and generated art is a question
that rule does not answer. Record what a thing is and where it came from in
the relevant Art/*/README.md before you run this, not after.
"""
import os
import sys

try:
    import bpy
except ImportError:
    sys.stderr.write(__doc__)
    raise SystemExit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'Art', 'Forged')
sys.path.insert(0, HERE)
from forge import PALETTE

# A BUDGET IN THE KITS' RANGE, not a number that sounds small. The forged
# pieces in this project run to a few hundred triangles; the CC0 creatures run
# to a few thousand. Twelve hundred sits inside that and is the default rather
# than a law: a thing with real silhouette in it can be given more.
BUDGET = 1200

# How much hue outweighs lightness when matching to the palette, and the sum
# below which a colour has no hue worth comparing. See `nearest`.
CHROMA = 30.0
LIGHT = 1.0
DIM = 0.06


def linear(c):
    """glTF and Blender hand back LINEAR already; sRGB inputs would not."""
    return max(0.0, min(1.0, c))


def nearest(rgb):
    """The palette entry closest to a colour, and how far off it was.

    HUE FIRST, LIGHTNESS SECOND, and that order is the whole of this function.

    The obvious thing is distance in RGB, and it was tried. A goblin reads
    (0.137, 0.192, 0.030) in linear, which is a dark green; this palette has no
    dark green, and the nearest entry by plain distance is `CrustBurnt`, a
    BROWN of the same lightness, at 0.20 while the only real green sits 0.85
    away. The arithmetic was right and the answer was a brown goblin, because
    plain distance trades hue for lightness at par and the eye does not.

    So the comparison is made on CHROMATICITY -- the colour with its
    brightness divided out -- and lightness is allowed only a small say. A
    dark green then lands on the palette's green and comes out lighter, which
    is a thing anybody can look at and accept, rather than on a brown, which
    is a thing nobody would.

    Below `DIM` there is no hue left to speak of and the question really is
    lightness, so near-blacks and near-whites are matched on that alone.
    """
    r, g, b = rgb
    tot = r + g + b
    out, gap = None, 1e9
    for name, (pr, pg, pb) in PALETTE.items():
        ptot = pr + pg + pb
        if tot <= DIM or ptot <= DIM:
            # one of them has no hue: compare what they do have
            d = 3.0 * (tot - ptot) ** 2
        else:
            d = (CHROMA * ((r / tot - pr / ptot) ** 2
                           + (g / tot - pg / ptot) ** 2
                           + (b / tot - pb / ptot) ** 2)
                 + LIGHT * ((tot - ptot) / 3.0) ** 2)
        if d < gap:
            out, gap = name, d
    return out, gap ** 0.5


def colour_of(mat):
    """One colour for a material: its base factor, or the mean of its texture.

    A node tree is walked rather than guessed at. An image is averaged over
    the pixels that are not transparent, because a sheet is mostly empty and
    including it drags every colour toward whatever the empty is.
    """
    if mat is None or not mat.use_nodes:
        c = getattr(mat, 'diffuse_color', (0.5, 0.5, 0.5, 1.0)) if mat else (0.5,) * 4
        return (linear(c[0]), linear(c[1]), linear(c[2]))
    base = None
    for n in mat.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            base = n.inputs.get('Base Color')
            break
    if base is None:
        return (0.5, 0.5, 0.5)
    if base.is_linked:
        src = base.links[0].from_node
        if src.type == 'TEX_IMAGE' and src.image:
            px = list(src.image.pixels)
            tot = [0.0, 0.0, 0.0]
            n = 0
            # every sixteenth pixel: a quarter of a million samples answers the
            # same question as four million and does it in a blink.
            for i in range(0, len(px) - 4, 4 * 16):
                if px[i + 3] < 0.5:
                    continue
                tot[0] += px[i]
                tot[1] += px[i + 1]
                tot[2] += px[i + 2]
                n += 1
            if n:
                return tuple(linear(v / n) for v in tot)
        if src.type == 'RGB':
            o = src.outputs[0].default_value
            return (linear(o[0]), linear(o[1]), linear(o[2]))
        return (0.5, 0.5, 0.5)
    v = base.default_value
    return (linear(v[0]), linear(v[1]), linear(v[2]))


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    low = path.lower()
    if low.endswith(('.glb', '.gltf')):
        bpy.ops.import_scene.gltf(filepath=path)
    elif low.endswith('.obj'):
        bpy.ops.wm.obj_import(filepath=path)
    elif low.endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        raise SystemExit('normalise: cannot read %s' % path)
    return [o for o in bpy.data.objects if o.type == 'MESH']


def repalette(meshes, word, keep):
    """Every material becomes a palette entry, or keeps its own colour.

    Returns the rows for the report and, when keeping, the colours to write
    beside the mesh for dress_normalised.py.
    """
    seen, rows, kept = {}, [], {}
    for o in meshes:
        for slot in o.material_slots:
            m = slot.material
            if m is None or m.name in seen:
                if m is not None:
                    slot.material = seen[m.name]
                continue
            rgb = colour_of(m)
            if keep:
                # NAMED FOR THE THING AND ITS SLOT, so two creatures that both
                # have a `Body` do not share one material and one colour.
                name = '%s_%s' % (word, m.name.split('.')[0])
                kept[name] = [round(c, 4) for c in rgb]
                gap = 0.0
            else:
                name, gap = nearest(rgb)
            # One Blender material per palette entry, named for it, so the OBJ
            # writes `usemtl Feather` and dress_forged.py knows what to do.
            made = bpy.data.materials.get(name) or bpy.data.materials.new(name)
            made.use_nodes = False
            made.diffuse_color = tuple(PALETTE[name] if not keep else rgb) + (1.0,)
            rows.append((m.name, name, gap))
            seen[m.name] = made
            slot.material = made
    return rows, kept


def decimate(meshes, budget):
    tris = 0
    for o in meshes:
        tris += sum(max(len(p.vertices) - 2, 1) for p in o.data.polygons)
    if tris <= budget:
        return tris, tris
    ratio = float(budget) / float(tris)
    for o in meshes:
        mod = o.modifiers.new('normalise', 'DECIMATE')
        mod.ratio = ratio
    return tris, budget


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if len(argv) < 3:
        sys.stderr.write(__doc__)
        raise SystemExit(2)
    src, word, tall = argv[0], argv[1], float(argv[2])
    budget = BUDGET
    if '--budget' in argv:
        budget = int(argv[argv.index('--budget') + 1])
    keep = '--keep' in argv

    meshes = load(src)
    if not meshes:
        raise SystemExit('normalise: %s has no mesh' % src)

    rows, kept = repalette(meshes, word, keep)
    was, now = decimate(meshes, budget)

    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, word + '.obj')

    def write(g):
        bpy.ops.wm.obj_export(
            filepath=dest, export_selected_objects=True, apply_modifiers=True,
            export_materials=True, export_triangulated_mesh=True,
            forward_axis='Y', up_axis='Z', global_scale=g)

    def height():
        lo, hi = 1e9, -1e9
        with open(dest) as f:
            for line in f:
                if line.startswith('v '):
                    z = float(line.split()[3])
                    lo, hi = min(lo, z), max(hi, z)
        return hi - lo if hi > lo else 0.0

    # FITTED TO THE WRITTEN FILE, for the reason posebake.py gives at length:
    # the arithmetic that says one pass should land it does not, and the file
    # can simply be measured.
    write(100.0)
    got = height()
    if got > 0.0:
        write(100.0 * (tall / got))
        got = height()

    if kept:
        import json
        side = os.path.join(OUT, word + '.colours.json')
        json.dump(kept, open(side, 'w'), indent=1)

    print('--- normalise %s -> Art/Forged/%s.obj' % (os.path.basename(src), word))
    print('    %.1f cm tall, %d triangles (was %d), colour %s'
          % (got, now, was, 'kept' if keep else 'matched to the palette'))
    for was_name, now_name, gap in rows:
        if keep:
            print('    %-28s -> %s' % (was_name, now_name))
            continue
        # A GAP WORTH LOOKING AT. Matching is on chromaticity, so the number is
        # not a distance in any familiar space; what matters is the comparison
        # between rows. Past about 0.7 the palette simply had no hue like this
        # one, and for anything alive that is the sign to use --keep instead.
        flag = '   <- the palette has no hue like this' if gap > 0.70 else ''
        print('    %-28s -> %-12s %.2f%s' % (was_name, now_name, gap, flag))


# Guarded, so the colour matching can be imported and questioned on its own.
# Blender runs a --python script as __main__, so this costs nothing here.
if __name__ == '__main__':
    main()
