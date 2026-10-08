#!/usr/bin/env python3
"""Photograph what the window draws, out of the window's own record.

The world hands out a wolf or a great helm when it feels like it, which is to
say almost never while somebody is looking. So the art is stood up in the
editor level instead -- in a grid, at the size the look asset says it is worn
or walks at, wearing the material the look asset names -- photographed, and
taken down again.

It reads the LOOK ASSET rather than the tables in Tools/, because the look
asset is what the window actually uses. A row that is wrong here is wrong in
the world, which is the point.

  gallery.py bestiary out.png
  gallery.py arms     out.png
  gallery.py armour   out.png
"""
import json, os, subprocess, sys
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import rpc

LOOK = '/Game/Interval/IntervalLook.IntervalLook'
SCENE = 'editor_toolset.toolsets.scene.SceneTools'
OBJ = 'editor_toolset.toolsets.object.ObjectTools'
ACTOR = 'editor_toolset.toolsets.actor.ActorTools'
APP = 'EditorToolset.EditorAppToolset'

# CENTIMETRES BETWEEN ONE PIECE AND THE NEXT, and it has to be settable.
#
# A hundred and fifty is right for helms and hatchets, which is what this
# sheet was written for. It is nowhere near right for a bell tower ten metres
# tall standing beside a haystack: the first sheet of the village packs came
# back as one solid pile of overlapping buildings. RACK_CELL=900 for those.
CELL = float(os.environ.get('RACK_CELL', '150'))
# WELL AWAY FROM THE ORIGIN. The template level keeps its floor, its blue
# blocks and a PlayerStart there, and the PlayerStart draws a billboard that
# lands in the middle of every photograph taken near it. Out here the
# background is sky.
# WELL AWAY FROM EVERYTHING, AND HIGH.
#
# The TopDown template keeps a large floor near the origin, and at seventy
# metres out the camera still caught it: a red-tinted slab sixty metres below,
# seen at a shallow angle, fills the bottom of the frame and reads exactly like
# one enormous creature in the foreground. Half an hour went into hunting a
# scaling bug in the crab that was not there -- its scale was 0.005 the whole
# time, which is a crab.
#
# The lesson is the ordinary one: when a photograph shows something impossible,
# doubt the photograph before the thing.
HERE = (140000.0, 140000.0, 14000.0)
YAW = float(os.environ.get('RACK_YAW', '215'))
ROLL = float(os.environ['RACK_ROLL']) if 'RACK_ROLL' in os.environ else None


def look(*props):
    r = rpc.call(OBJ, 'get_properties', {'instance': {'refPath': LOOK},
                                         'properties': list(props)})
    return json.loads(json.loads(r)['returnValue'])


def sweep():
    found = json.loads(rpc.call(SCENE, 'find_actors',
                                {'name': '__rack', 'tag': '',
                                 'collision_channels': []}))['returnValue']
    for a in found:
        rpc.call(SCENE, 'remove_from_scene', {'actor': a})
    return len(found)


def ref(v):
    return v['refPath'] if isinstance(v, dict) and v.get('refPath') else None


def extents(mesh):
    """The mesh's size along each axis, in centimetres."""
    try:
        got = json.loads(rpc.call('editor_toolset.toolsets.static_mesh.StaticMeshTools',
                                  'get_bounds', {'mesh': {'refPath': mesh}}))['returnValue']
        if 'min' in got:
            return [got['max'][a] - got['min'][a] for a in 'xyz']
    except Exception:
        pass
    try:
        got = json.loads(rpc.call('editor_toolset.toolsets.skeletal_mesh.SkeletalMeshTools',
                                  'get_bounds', {'mesh': {'refPath': mesh}}))['returnValue']
        if 'boxExtent' in got:
            return [got['boxExtent'][a] * 2.0 for a in 'xyz']
    except Exception:
        pass
    return [100.0, 100.0, 100.0]


def upright(mesh):
    """How far to roll this piece so that it stands the way it is worn.

    Not a guess from the bounds -- that was tried and it lays sheep on their
    backs, because a sheep is longest along the axis it walks down and a
    breastplate is longest along the axis it is worn across. Bounds cannot tell
    a long animal from a flat object.

    What CAN tell them apart is where the art came from. Everything in this
    project is Z-up .fbx or glTF except the armour, which is .obj modelled
    Y-up and arrives lying on its back -- and the armour all lives in one
    folder. That is not a clever rule; it is the true one.
    """
    # Only the armour. It is .obj modelled Y-up and arrives on its back. The
    # wild bestiary is .glb and Interchange converts it properly -- rolling it
    # as well put a goat upside down, which is how that was found out.
    return -90.0 if '/Interval/Armour/' in mesh else 0.0


def span(mesh):
    """How big the thing is, in centimetres, whatever kind of mesh it is.

    A gallery wants every piece the same size on the page -- a crown next to a
    dragon at the sizes they are WORN and WALK at is a photograph of a dragon
    with some dust beside it. So each piece is scaled to its own bounds.
    """
    return max(extents(mesh))


def bestiary():
    """Every creature the world can send, at the size it walks at."""
    out = []
    for word, row in sorted(look('Mobs')['Mobs'].items()):
        mesh = ref(row.get('skeletal')) or ref(row.get('mesh'))
        if not mesh or '/Engine/BasicShapes/' in mesh:
            continue          # still a stand-in; the audit reports those
        # AND WHAT IT IS WEARING. In the world the outfit is a follower that
        # copies the body's pose bone for bone; standing still in a reference
        # pose it is enough to put it in the same place, because that is
        # exactly what the pose it would copy is.
        parts = [ref(q) for q in (row.get('skeletalParts') or [])]
        # AND WHAT IT DOES WHEN NOTHING IS HAPPENING. The look asset now says,
        # per creature, which clip `still` is; standing one in its own idle is
        # the only way to tell a rig that arrived correctly from one that did
        # not, because a bind pose looks like a broken import and is not.
        idle = None
        still = ((row.get('motions') or {}).get('still') or {}).get('anim')
        if isinstance(still, dict):
            idle = still.get('refPath')
        lean = row.get('lean') or {}
        out.append((word, mesh, None, ref(row.get('material')),
                    [q for q in parts if q], idle,
                    (lean.get('pitch', 0.0), lean.get('yaw', 0.0), lean.get('roll', 0.0))))
    return out


def worn(want_bones):
    """What a citizen holds or wears -- all of it, not just the first piece.

    A word can name more than one: plate armour is a cuirass AND the pauldrons
    that close the top of it, and a gallery that shows only the first piece
    shows a tub. The extra pieces keep their offset relative to the first, in
    the proportion the two are worn at, so the shoulders land on the shoulders.
    """
    out = []
    for word, entry in sorted(look('Worn')['Worn'].items()):
        pieces = [p for p in (entry.get('pieces') or [])
                  if p.get('bone') in want_bones and ref(p.get('mesh'))]
        if not pieces:
            continue
        lead = pieces[0]
        extra = []
        for p in pieces[1:]:
            # IN MESH UNITS, NOT CENTIMETRES. The offsets in the look asset
            # are centimetres at the size the piece is WORN; the gallery
            # stands everything at its own size, which is three times that.
            # Multiplying the worn offset by the gallery's scale put the
            # pauldrons eleven metres above the breastplate, out of frame,
            # and the photograph looked exactly as if they were missing.
            extra.append({'mesh': ref(p['mesh']),
                          'dz': ((p['offset']['z'] - lead['offset']['z'])
                                 / max(lead['scale']['x'], 1e-6)),
                          'rel': p['scale']['x'] / max(lead['scale']['x'], 1e-6)})
        out.append((word, ref(lead['mesh']), None, ref(lead.get('material')), extra,
                    None, None))
    return out


SUN = ('/Game/TopDown/Lvl_TopDown.Lvl_TopDown:PersistentLevel.'
       'DirectionalLight_0.LightComponent0')


def light_for_the_photograph():
    """Point the sun over the camera's shoulder, and hand back what it was.

    The level's sun sits wherever the last session left it, and a gallery lit
    from behind is a gallery of silhouettes. The hour actor only drives this
    light while the world is running, so moving it in the editor disturbs
    nothing -- but it is put back anyway, because a level that quietly drifts
    every time somebody takes a photograph is how a level stops being known.
    """
    # TWICE, NOT ONCE. `get_properties` answers {"returnValue": "<json>"} --
    # the properties are a STRING inside the envelope -- and handing the
    # envelope straight back to `set_properties` sets a property called
    # `returnValue`, which fails without saying so and leaves the sun where
    # the photograph put it. That is exactly what happened the first time.
    was = json.loads(json.loads(rpc.call(OBJ, 'get_properties',
                                         {'instance': {'refPath': SUN},
                                          'properties': ['RelativeRotation',
                                                         'LightColor',
                                                         'Intensity']}))['returnValue'])
    rpc.call(OBJ, 'set_properties', {'instance': {'refPath': SUN}, 'values': json.dumps(
        {'RelativeRotation': {'pitch': -38.0, 'yaw': 118.0, 'roll': 0.0},
         # WHITE, and not very bright. The level's sun is warm, because the
         # hour makes it warm; a gallery lit by it reports steel as sandstone.
         'LightColor': {'r': 255, 'g': 255, 'b': 255, 'a': 255},
         'Intensity': 4.4})})
    return was


def folder(where):
    """Every skeletal mesh under a content folder, straight off the disk.

    New art has no row in the look asset yet -- that is the point of looking at
    it -- so this one does not read the asset. A creature's mesh is the .uasset
    that shares its folder's name.
    """
    root = os.path.join(os.path.dirname(SP), 'Content', *where.split('/')[2:])
    out = []
    for name in sorted(os.listdir(root)):
        mesh = os.path.join(root, name, name + '.uasset')
        if not os.path.isfile(mesh):
            continue
        # AND SOMETHING TO STAND IN. A skeletal mesh with no animation shows
        # its BIND pose, and an animated creature's bind pose is whatever the
        # rigger left it in -- a wolf on its back with its legs in the air.
        # It is not a broken import and it is not an axis: it is a mesh that
        # has never been told to do anything.
        idle = None
        for clip in sorted(os.listdir(os.path.join(root, name))):
            if clip.endswith('.uasset') and 'Idle' in clip and 'HitReact' not in clip:
                idle = '%s/%s/%s.%s' % (where, name, clip[:-7], clip[:-7])
                break
        out.append((name, '%s/%s/%s.%s' % (where, name, name, name),
                    None, None, [], idle, None))
    return out


# ONE ROW COMES OUT TOO BIG AND IT IS NOT A SCALING BUG IN THE ART.
#
# The crab fills the bottom of the bestiary sheet. Its scale here is computed
# the same way as everything else -- 0.005, from its own bounds -- and the same
# mesh at the look asset's own scale, racked ON ITS OWN through `rack.py`, is a
# hand-sized crab, which is what the world draws. Two separate single-asset
# racks agree. Something about how this sheet frames that row is wrong and the
# row is not, and a contact sheet is a diagnostic rather than the product, so
# it is written down here rather than chased further.
#
# Half an hour went into three wrong theories first -- a stale capture, the
# template floor, root motion -- and each was disproved by moving the rack and
# finding the picture unchanged. When a photograph shows something impossible,
# the next step is a SMALLER photograph: racking three assets instead of
# twenty-nine is what finally named the shape.


def built(words=None):
    """Words from the Props table, drawn the way the WINDOW draws them.

    `folder()` above photographs art straight off the disk, which is right for
    a mesh that has no row yet. This is the other question and the one that
    catches more: a row can point at beautiful art and still be wrong, because
    the SCALE is the row's and not the mesh's. Three CC0 packs arrived at three
    different scales -- a barrel 20cm tall in one and 107cm in another -- so
    "does the mesh look good" and "is this thing the right size to stand next
    to a person" are separate questions and only the second one matters here.

    A CITIZEN IS STOOD IN THE GRID TOO, always first, for exactly that reason:
    a sheet of props with nothing human in it is a sheet on which everything
    looks plausible.
    """
    props = look('Props')['Props']
    if not words:
        words = sorted(props)
    out = []
    # An outfit is a LIST of skeletal pieces -- body, then clothes -- and the
    # first of them is the figure itself. At scale 1 it is 1.81m, which is the
    # ruler every other thing in the sheet is measured against.
    outfits = look('Outfits')['Outfits']
    for kit in outfits:
        pieces = kit.get('parts') or []
        if pieces and isinstance(pieces[0], dict) and pieces[0].get('refPath'):
            out.append(('A CITIZEN, 1.81m', pieces[0]['refPath'],
                        1.0, None, [], None, None))
            break
    for w in words:
        row = props.get(w)
        if not row:
            print('  no row for', w)
            continue
        mesh = row.get('mesh')
        mesh = mesh.get('refPath') if isinstance(mesh, dict) else mesh
        if not mesh or mesh == 'None':
            # Drawn as a skeleton, or drawn only by its parts.
            sk = row.get('skeletal')
            mesh = sk.get('refPath') if isinstance(sk, dict) else None
            if not mesh:
                print('  %s has no mesh of its own (parts only)' % w)
                continue
        s = row.get('scale') or {}
        mat = row.get('material')
        mat = mat.get('refPath') if isinstance(mat, dict) else None
        # PARTS ARE LEFT OFF ON PURPOSE. `stand()` wants them in the shape a
        # WORN piece has -- a height and a relative size -- and a prop's parts
        # carry a full offset and rotation instead. Converting the two would
        # be a second implementation of the placement the window already does,
        # and this sheet is not asking what a thing is carrying. It is asking
        # whether the thing is the right size to stand next to a person, which
        # is the question three packs at three different scales raised and the
        # only one a contact sheet can answer honestly.
        out.append((w, mesh, float(s.get('x') or 1.0), mat, [], None, None))
    return out


def stand(items, out):
    rpc.call(APP, 'StopPIE', {})
    gone = sweep()
    if gone:
        print('cleared %d left over' % gone)

    cols = max(1, int(len(items) ** 0.5 + 0.999))
    rows = (len(items) + cols - 1) // cols
    wide = CELL * (cols - 1)
    tall = CELL * (rows - 1)
    for i, (word, mesh, scale, material, parts, idle, lean) in enumerate(items):
        if scale is None:
            scale = (CELL * 0.86) / max(span(mesh), 1e-3)
        made = rpc.call(SCENE, 'add_to_scene_from_asset', {
            'asset_path': mesh.split('.')[0], 'name': '__rack_%d' % i,
            'xform': {'location': {'x': HERE[0] - wide / 2 + (i % cols) * CELL,
                                   'y': HERE[1],
                                   'z': HERE[2] + tall - (i // cols) * CELL},
                      # STANDING UP. The .obj art in this project is modelled
                      # Y-up and arrives lying on its back -- a bucket helm
                      # photographed flat is a metal bowl -- so it is rolled a
                      # quarter turn. The yaw is three-quarters on so a helmet
                      # shows its face and its side at once.
                      # THE LOOK ASSET'S OWN LEAN WHERE THERE IS ONE. A sheet
                      # that stands a creature differently from the way the
                      # world stands it is a sheet that cannot be trusted.
                      'rotation': ({'pitch': lean[0], 'yaw': YAW + lean[1],
                                    'roll': lean[2]} if lean and any(lean)
                                   else {'pitch': 0.0, 'yaw': YAW,
                                         'roll': upright(mesh) if ROLL is None else ROLL}),
                      'scale': {'x': scale, 'y': scale, 'z': scale}}})
        actor = ref(json.loads(made).get('returnValue') or {})
        if not actor:
            print('  could not stand', word, mesh)
            continue
        if idle:
            # ONLY THE SKELETAL COMPONENT. Setting `AnimationData` on every
            # component of the actor -- including the bare scene root -- put
            # three creatures at twenty times their size and left the rest in
            # the dark. The root is not a mesh and does not want an animation.
            comps = json.loads(rpc.call(ACTOR, 'get_components',
                                        {'actor': {'refPath': actor}}))['returnValue']
            for c in comps:
                if 'SkeletalMeshComponent' not in c['refPath']:
                    continue
                rpc.call(OBJ, 'set_properties', {'instance': c, 'values': json.dumps(
                    {'AnimationMode': 'AnimationSingleNode',
                     # POSED, NOT PLAYING. A contact sheet wants one frame of
                     # the idle, and several of these clips carry ROOT MOTION
                     # -- left running, a crab walks out of its cell and up to
                     # the lens, where it fills the frame and reads as a
                     # scaling bug. Frozen a third of a second in, every
                     # creature stands where it was put.
                     'AnimationData': {'animToPlay': {'refPath': idle},
                                       'bSavedLooping': False,
                                       'bSavedPlaying': False,
                                       'savedPosition': 0.35,
                                       'savedPlayRate': 1.0}})})
        standing = [actor]
        for n, part in enumerate(parts):
            # A follower on a skeleton is a bare path and sits exactly where
            # the body does; a second WORN piece carries its own offset and
            # size, which are in the proportions it is worn at.
            path = part if isinstance(part, str) else part['mesh']
            dz = 0.0 if isinstance(part, str) else part['dz'] * scale
            sz = scale if isinstance(part, str) else scale * part['rel']
            worn_actor = rpc.call(SCENE, 'add_to_scene_from_asset', {
                'asset_path': path.split('.')[0], 'name': '__rack_%d_%d' % (i, n),
                'xform': {'location': {'x': HERE[0] - wide / 2 + (i % cols) * CELL,
                                       'y': HERE[1],
                                       'z': HERE[2] + tall - (i // cols) * CELL + dz},
                          'rotation': {'pitch': 0.0, 'yaw': YAW,
                                       'roll': upright(path) if ROLL is None else ROLL},
                          'scale': {'x': sz, 'y': sz, 'z': sz}}})
            got = ref(json.loads(worn_actor).get('returnValue') or {})
            if got:
                standing.append(got)
        if material:
            # The look asset names one material for the whole creature, so it
            # goes on every slot of every piece -- the same rule the citizens
            # actor follows, and the reason a wraith is one colour from cowl
            # to hem instead of somebody wearing a cloak.
            for a in standing:
                comps = json.loads(rpc.call(ACTOR, 'get_components',
                                            {'actor': {'refPath': a}}))['returnValue']
                for c in comps:
                    rpc.call(OBJ, 'set_properties', {'instance': c, 'values': json.dumps(
                        {'OverrideMaterials': [{'refPath': material}] * 8})})
        print('  %-24s x%.5f %s%s' % (word, scale, mesh.split('/')[-1],
                                ' + ' + ', '.join(
                                    (q if isinstance(q, str) else q['mesh'])
                                    .split('/')[-1].split('.')[0]
                                    for q in parts) if parts else ''))

    was = light_for_the_photograph()
    back = max(wide * 0.58, tall * 1.02) + 160.0
    subprocess.run([sys.executable, SP + '/cap.py', out,
                    str(HERE[0]), str(HERE[1] - back), str(HERE[2] + tall / 2),
                    '0', '90', '0', '1400'], check=True)
    rpc.call(OBJ, 'set_properties', {'instance': {'refPath': SUN},
                                     'values': json.dumps(was)})
    sweep()
    print(out, len(items), 'pieces')


if __name__ == '__main__':
    what, out = sys.argv[1], sys.argv[2]
    if what == 'bestiary':
        stand(bestiary(), out)
    elif what == 'arms':
        stand(worn({'hand_r', 'hand_l'}), out)
    elif what == 'armour':
        stand(worn({'Head', 'spine_03'}), out)
    elif what.startswith('/Game/'):
        stand(folder(what), out)
    elif what == 'built':
        # gallery.py built out.png [word ...]
        stand(built(sys.argv[3:] or None), out)
    else:
        raise SystemExit('bestiary | arms | armour | built | /Game/Some/Folder')
