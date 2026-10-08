"""A mesh forge: geometry authored from code, for words no kit has art for.

WHY THIS EXISTS.

This window draws from CC0 kits, and a handful of the world's words have no
mesh in any of them -- four animal masks, leg armour, a heap of bones, a siege
engine. Those were reported as "still waiting for art", with the primitives
standing in for them defended as honest on the grounds that a horn is a cone.
Two answers came back, and both were right:

    "we can't use weapons as cylinders or cubes that's just .. no go"

    "We can't really like design any items ourselves? Like how in the other
     web windows anything could just be drawn"

The second is the important one. A window drawing in two dimensions can draw
any shape it likes; being unable to show a wolf mask is a limit this project
imposed on itself by only ever LOOKING for art. An OBJ is a text file. A
generator that can revolve a profile, extrude an outline and sweep a tube can
make a mask, a horn, a greave or a pile of bones, and it needs nothing
installed -- no Blender, no numpy, no pack to download and no licence to read,
because the geometry is this project's own.

This is the same move the project already made twice: the ground is authored
in `ground.hlsl` rather than textured, and the props are authored in tables
rather than placed by hand. Art is the third.

HOW IT IS USED. Build a `Mesh`, add surfaces to it, write it out:

    m = Mesh()
    m.lathe(HORN_PROFILE, segments=12, material='Bone')
    m.write(ART / 'horn.obj')

CONVENTIONS. Centimetres, Z up, X forward -- the same as everything else in
this project and the same as Unreal. Faces are quads where the surface is a
grid and triangles at the caps; both are legal OBJ and Unreal triangulates on
import. Materials are named groups with a flat colour in the .mtl beside it,
which is exactly how the Quaternius kits are built, so the results sit beside
them without looking borrowed.
"""
import math
import os

# The palette. Flat colours, named the way the CC0 kits name theirs, so that a
# mesh forged here and a mesh out of a pack can share a material convention.
# Values are linear RGB in 0..1, which is what an .mtl's `Kd` is.
PALETTE = {
    'Bone':      (0.839, 0.812, 0.706),
    'BoneDark':  (0.671, 0.639, 0.545),
    'Wood':      (0.400, 0.267, 0.157),
    'WoodDark':  (0.278, 0.180, 0.106),
    'Iron':      (0.353, 0.365, 0.396),
    'Steel':     (0.541, 0.565, 0.600),
    'Gold':      (0.769, 0.588, 0.208),
    # OLD iron, which is a different colour from iron. The chain in this world
    # is the one thing gold cannot buy and it is not a new-forged thing: it
    # comes out of the ground, and iron that has been in the ground is the
    # red-brown of oxide, not the blue-grey of a blade.
    'Rust':      (0.404, 0.235, 0.145),
    'Fur':       (0.412, 0.322, 0.255),
    'FurLight':  (0.647, 0.561, 0.471),
    'FurDark':   (0.208, 0.180, 0.161),
    'Feather':   (0.149, 0.145, 0.169),
    'Leather':   (0.329, 0.231, 0.149),
    'Cloth':     (0.616, 0.573, 0.494),
    # Silk. Nearly white and very slightly blue, which is what a web looks like
    # against grass: it is not a colour so much as a lack of one.
    'Silk':      (0.871, 0.886, 0.902),
    # NOT 'Horn'. A material and a mesh cannot share a name in Unreal --
    # case-insensitively -- and the material wins, so `horn.obj` imported
    # its materials and then had nowhere to put the mesh. The same
    # collision renamed the Medieval Village pack's Bell mesh to Bell1.
    'Keratin':   (0.239, 0.220, 0.192),

    # ---- THE GOODS ----
    #
    # THE NAMES HERE MAY NOT BE ITEM NAMES. `dress_forged.py` makes one
    # material asset per key in this dict and puts it in the same folder as the
    # forged meshes, and Unreal treats asset names as case-INSENSITIVE: a
    # colour called `Coal` and a mesh called `coal` are the same name, the
    # material wins, and every lookup of the mesh quietly returns a material.
    # Thirteen goods failed to render that way, each with an error about a
    # material having no bounding box. So the ore is `Soot`, the ale is
    # `AleBrown`, the wool is `Fleece` -- which is also why the horn's colour
    # above is `Keratin`.
    #
    # Everything above dresses a person; everything below is what the world is
    # made of. They live in the same dict because `dress_forged.py` reads THIS
    # dict to rebuild the material instances, and a colour declared anywhere
    # else arrives in Unreal as grey -- which is how the first run of the goods
    # came back as forty-nine identical lumps of putty.

    'Rock':       (0.353, 0.345, 0.333),
    'RockDark':   (0.243, 0.239, 0.235),
    'IronOre':    (0.404, 0.298, 0.243),
    'GoldOre':    (0.514, 0.459, 0.298),
    'Soot':       (0.114, 0.110, 0.118),
    'Sulphur':  (0.706, 0.596, 0.196),
    'Nitre':  (0.831, 0.816, 0.769),
    'Silver':     (0.659, 0.671, 0.678),
    'Ember':      (0.780, 0.318, 0.129),
    'Oak':        (0.490, 0.357, 0.208),
    'Heartgrain':  (0.412, 0.204, 0.176),
    'BarkIron':   (0.294, 0.298, 0.286),
    'Bark':       (0.302, 0.224, 0.149),
    'Plank':      (0.616, 0.475, 0.302),
    'Fish':       (0.522, 0.573, 0.588),
    'FishCooked': (0.737, 0.569, 0.376),
    'FishBurnt':  (0.161, 0.137, 0.129),
    'FishSalt':   (0.780, 0.784, 0.745),
    'EelSkin':        (0.243, 0.290, 0.259),
    'EelSmoked':  (0.357, 0.259, 0.180),
    'Shell':      (0.760, 0.482, 0.365),
    'Crust':      (0.749, 0.561, 0.318),
    'CrustBurnt': (0.180, 0.145, 0.125),
    'AleBrown':        (0.573, 0.361, 0.133),
    'Pottage':      (0.667, 0.482, 0.243),
    'PottageDeep':  (0.302, 0.404, 0.427),
    'Water':      (0.639, 0.784, 0.812),
    'Wheat':      (0.804, 0.686, 0.361),
    'Meal':      (0.886, 0.867, 0.812),
    'Fleece':       (0.871, 0.855, 0.816),
    'Herb':     (0.396, 0.514, 0.267),
    'Vellum':     (0.847, 0.796, 0.667),
    'Wax':        (0.659, 0.184, 0.161),
    'Powder':     (0.216, 0.208, 0.200),
    'Sack':       (0.545, 0.463, 0.333),
    'Magic':      (0.435, 0.353, 0.663),
    'Fletch':     (0.784, 0.769, 0.729),
}


class Mesh:
    """Vertices, faces and which material each face belongs to."""

    def __init__(self):
        self.v = []                  # [(x, y, z), ...]
        self.faces = []              # [(material, (i, j, k[, l])), ...]

    # ---- the primitives of the forge -------------------------------------

    def _add(self, p):
        self.v.append(p)
        return len(self.v)           # OBJ indices are 1-based

    def quad(self, a, b, c, d, material):
        self.faces.append((material, (a, b, c, d)))

    def tri(self, a, b, c, material):
        self.faces.append((material, (a, b, c)))

    def lathe(self, profile, segments=12, material='Bone',
              origin=(0.0, 0.0, 0.0), sweep=360.0, cap=True):
        """Revolve a profile about Z.

        `profile` is [(radius, z), ...] read bottom to top. This is how a horn,
        a bone's shaft, a helmet's dome and a pot are all the same operation --
        which is most of the reason a forge is worth having at all.
        """
        ox, oy, oz = origin
        full = abs(sweep - 360.0) < 1e-6
        rings = []
        n = segments if full else segments + 1
        for r, z in profile:
            ring = []
            for s in range(n):
                a = math.radians(sweep * s / segments)
                ring.append(self._add((ox + r * math.cos(a),
                                       oy + r * math.sin(a),
                                       oz + z)))
            rings.append(ring)
        for i in range(len(rings) - 1):
            lo, hi = rings[i], rings[i + 1]
            for s in range(len(lo) if full else len(lo) - 1):
                t = (s + 1) % len(lo)
                self.quad(lo[s], lo[t], hi[t], hi[s], material)
        if cap:
            for ring, flip in ((rings[0], True), (rings[-1], False)):
                r = profile[0][1] if flip else profile[-1][1]
                mid = self._add((ox, oy, oz + (profile[0][1] if flip
                                               else profile[-1][1])))
                for s in range(len(ring) if full else len(ring) - 1):
                    t = (s + 1) % len(ring)
                    if flip:
                        self.tri(mid, ring[t], ring[s], material)
                    else:
                        self.tri(mid, ring[s], ring[t], material)
        return rings

    def plate(self, outline, thickness, material='Bone', origin=(0.0, 0.0, 0.0)):
        """Extrude a closed 2D outline along X, giving it a front and a back.

        `outline` is [(y, z), ...] anticlockwise. A mask is a plate; so is a
        shoulder guard and a signboard.
        """
        ox, oy, oz = origin
        h = thickness / 2.0
        front = [self._add((ox + h, oy + y, oz + z)) for y, z in outline]
        back = [self._add((ox - h, oy + y, oz + z)) for y, z in outline]
        n = len(outline)
        for i in range(n):
            j = (i + 1) % n
            self.quad(front[i], front[j], back[j], back[i], material)
        # Fan the caps from the centroid, which is correct for any convex or
        # mildly concave outline and is all these need.
        for ring, sign in ((front, 1), (back, -1)):
            cy = sum(y for y, _ in outline) / n
            cz = sum(z for _, z in outline) / n
            mid = self._add((ox + sign * h, oy + cy, oz + cz))
            for i in range(n):
                j = (i + 1) % n
                if sign > 0:
                    self.tri(mid, ring[i], ring[j], material)
                else:
                    self.tri(mid, ring[j], ring[i], material)
        return front, back

    def tube(self, path, radii, segments=8, material='Bone'):
        """Sweep a circle along a polyline. Bones, chains, antlers, hafts."""
        if isinstance(radii, (int, float)):
            radii = [radii] * len(path)
        rings = []
        for i, (p, r) in enumerate(zip(path, radii)):
            nxt = path[min(i + 1, len(path) - 1)]
            prv = path[max(i - 1, 0)]
            d = [nxt[k] - prv[k] for k in range(3)]
            ln = math.sqrt(sum(c * c for c in d)) or 1.0
            d = [c / ln for c in d]
            # Any vector not parallel to the direction gives a usable frame.
            up = (0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (1.0, 0.0, 0.0)
            u = _cross(d, up)
            u = _norm(u)
            w = _norm(_cross(d, u))
            ring = []
            for s in range(segments):
                a = 2.0 * math.pi * s / segments
                ring.append(self._add(tuple(
                    p[k] + r * (math.cos(a) * u[k] + math.sin(a) * w[k])
                    for k in range(3))))
            rings.append(ring)
        for i in range(len(rings) - 1):
            lo, hi = rings[i], rings[i + 1]
            for s in range(segments):
                t = (s + 1) % segments
                self.quad(lo[s], lo[t], hi[t], hi[s], material)
        for ring, flip in ((rings[0], True), (rings[-1], False)):
            cx = sum(self.v[i - 1][0] for i in ring) / segments
            cy = sum(self.v[i - 1][1] for i in ring) / segments
            cz = sum(self.v[i - 1][2] for i in ring) / segments
            mid = self._add((cx, cy, cz))
            for s in range(segments):
                t = (s + 1) % segments
                if flip:
                    self.tri(mid, ring[t], ring[s], material)
                else:
                    self.tri(mid, ring[s], ring[t], material)
        return rings

    def blob(self, centre, radius, material='Bone', rings=5, segments=8,
             squash=(1.0, 1.0, 1.0), seed=0):
        """A lumpy sphere. Skulls, stones, a heap of anything."""
        cx, cy, cz = centre
        sx, sy, sz = squash
        grid = []
        for i in range(rings + 1):
            phi = math.pi * i / rings
            ring = []
            for s in range(segments):
                a = 2.0 * math.pi * s / segments
                # A little deterministic wobble, so two skulls are not the same
                # skull and nothing here needs a random number generator.
                k = math.sin((i * 7 + s * 13 + seed * 31) * 1.7) * 0.07
                r = radius * (1.0 + k)
                ring.append(self._add((
                    cx + sx * r * math.sin(phi) * math.cos(a),
                    cy + sy * r * math.sin(phi) * math.sin(a),
                    cz + sz * r * math.cos(phi))))
            grid.append(ring)
        for i in range(rings):
            lo, hi = grid[i], grid[i + 1]
            for s in range(segments):
                t = (s + 1) % segments
                self.quad(lo[s], lo[t], hi[t], hi[s], material)
        return grid

    # ---- writing it out ---------------------------------------------------

    def write(self, path, name=None):
        name = name or os.path.splitext(os.path.basename(path))[0]
        mtl = os.path.splitext(path)[0] + '.mtl'
        used = []
        for m, _ in self.faces:
            if m not in used:
                used.append(m)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(mtl, 'w') as f:
            f.write('# forged by Tools/forge.py\n')
            for m in used:
                r, g, b = PALETTE.get(m, (0.7, 0.7, 0.7))
                f.write('\nnewmtl %s\n' % m)
                f.write('Kd %.6f %.6f %.6f\n' % (r, g, b))
                f.write('Ka 0.000000 0.000000 0.000000\n')
                f.write('Ks 0.100000 0.100000 0.100000\n')
                f.write('Ns 24.000000\nd 1.000000\nillum 2\n')
        with open(path, 'w') as f:
            f.write('# forged by Tools/forge.py -- geometry authored from code,\n'
                    '# because a word with no art in any kit is not a word this\n'
                    '# window is allowed to leave as a cube.\n')
            f.write('mtllib %s\n' % os.path.basename(mtl))
            f.write('o %s\n' % name)
            for x, y, z in self.v:
                f.write('v %.4f %.4f %.4f\n' % (x, y, z))
            for m in used:
                f.write('usemtl %s\n' % m)
                for mat, idx in self.faces:
                    if mat != m:
                        continue
                    f.write('f ' + ' '.join(str(i) for i in idx) + '\n')
        return path


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(a):
    ln = math.sqrt(sum(c * c for c in a)) or 1.0
    return tuple(c / ln for c in a)
