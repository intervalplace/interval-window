# THE INVENTORY SPRITES, PHOTOGRAPHED FROM THE THINGS THEMSELVES.
#
# The pack drew each item as the first letter of its name -- arrows were a
# letter A -- which is a stand-in and reads as one. The question was where
# sprites come from, and the answer is that for most of this vocabulary they do
# not need drawing at all: eighty-one of the world's hundred and thirty items
# already have a real mesh in this project, because somebody is wearing or
# wielding one. A sword in the pack should be the same sword that is on the
# citizen's back. So the icons are RENDERED from the meshes, which is how the
# window this one is modelled on made its own.
#
# THE LIGHTING IS NOT THE WORLD'S. The obvious way to do this is to photograph
# the item where it stands and keep the frame, and the first attempt did: it
# came back a sword at midnight on a navy sky, because the world it was
# standing in had a time of day. An icon cannot depend on the hour.
#
# So no photograph of a lit scene is kept at all. Three passes are taken --
# BASE COLOUR, which is the albedo with no light on it; NORMAL, which is the
# direction each pixel faces; and DEVICE DEPTH -- and the shading is done
# afterwards, in `matte.py`, from a light this project chooses. The world's
# sun, sky, fog and exposure are all absent by construction, so the same item
# renders identically at noon, at midnight and in the rain.
#
# And the depth pass is the matte. Unreal draws depth reversed, so the value is
# exactly zero everywhere nothing was drawn and greater than zero on the item:
# a clean silhouette for nothing, with no keying colour to pick and no fringe
# to clean up.
#
# NOTHING IN THE LEVEL IS TOUCHED. The capture is given a show-only list of one
# actor, so the world it is standing in -- a fully built settlement -- is not in
# the picture and does not have to be unloaded or reloaded to take it.
#
#   exec py .../icons.py            (through playremote, with PIE stopped)
import json, math, os, sys, unreal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# RELOADED, NOT JUST IMPORTED. This runs inside the editor's own interpreter,
# which lives for the length of the session -- so `import tiers` after the
# first render returns the module as it was hours ago. Every edit to the tier
# table was silently ignored, and the renders that were supposed to prove the
# grades apart were made with the table the grades started with.
import importlib
import tiers as _tiers
importlib.reload(_tiers)
tier_of, is_metal = _tiers.tier_of, _tiers.is_metal

S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
     'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')
OUT = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'Icons', 'raw'))
SIDE = 512          # rendered big and reduced later: the reduction IS the anti-aliasing
FAR = 200000.0      # where the item is stood, well clear of the world

report = {'done': [], 'errors': [], 'by_slot': [], 'spread': {}}


def note(m):
    unreal.log('ICONS ' + m)


def world():
    es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    return es.get_game_world() or es.get_editor_world()


def target():
    # Through the library, not by constructing one: a bare TextureRenderTarget2D
    # is never initialised and has no resource behind it.
    return unreal.RenderingLibrary.create_render_target2d(
        world(), SIDE, SIDE, unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0, 0, 0, 1), False)


def spread(w, target):
    """How far apart the colour channels are, over what was actually drawn.

    Zero is the DEFAULT material's signature. A material's shader is compiled
    the first time something asks to draw it, and until it is ready the mesh
    draws with `M_IntervalFlat`'s own defaults, which are exactly neutral --
    so an item whose every drawn pixel has red, green and blue equal is an
    item whose shader was not ready, and not an item that is grey. Nothing in
    this world is exactly neutral: the greyest real things here, rubble and
    coal, come back at one and two, because no entry in the forge palette is
    neutral and the light is not either.

    Sampled on a grid rather than read whole. The question is only whether to
    take the picture again, and a thousand pixels answer it as well as a
    quarter of a million would.
    """
    ground = unreal.RenderingLibrary.read_render_target_pixel(w, target, 0, 0)
    seen = total = 0
    step = max(1, SIDE // 32)
    for y in range(0, SIDE, step):
        for x in range(0, SIDE, step):
            p = unreal.RenderingLibrary.read_render_target_pixel(w, target, x, y)
            if p.r == ground.r and p.g == ground.g and p.b == ground.b:
                continue                      # the empty frame round the item
            total += max(p.r, p.g, p.b) - min(p.r, p.g, p.b)
            seen += 1
    return (total / seen) if seen else None


def fills(w, target):
    """How much of the frame the thing actually drew into, 0 to 1.

    THE BOUNDS OF A SKELETAL MESH ARE A LIE, and this is the answer to it.
    `get_bounds` reports the ANIMATED extent, so a clip that translates the
    root makes the box enormous: `Risen_Male` framed a camera for a box many
    times the creature and drew it at 94 lit pixels out of 16,384, which is
    six tenths of one per cent of its own sprite. `barrow-wight`, `risen` and
    `incursion` share that mesh and all three came back with the same 94.
    `Tools/bestiary.py` warned about exactly this and measures the glTF's own
    accessor bounds instead, which is not available from in here.

    So nothing is trusted: the thing is photographed once, what it drew is
    measured, and the frame is corrected from that. It is exact for any mesh
    of any kind, animated or not, and it costs one capture.

    Sampled on the same grid `spread` uses, for the same reason.
    """
    ground = unreal.RenderingLibrary.read_render_target_pixel(w, target, 0, 0)
    step = max(1, SIDE // 48)
    lo_x = lo_y = SIDE
    hi_x = hi_y = -1
    for y in range(0, SIDE, step):
        for x in range(0, SIDE, step):
            p = unreal.RenderingLibrary.read_render_target_pixel(w, target, x, y)
            if p.r == ground.r and p.g == ground.g and p.b == ground.b:
                continue
            if x < lo_x: lo_x = x
            if x > hi_x: hi_x = x
            if y < lo_y: lo_y = y
            if y > hi_y: hi_y = y
    if hi_x < 0:
        return None
    # DID IT RUN OFF THE EDGE. A thing bigger than the frame has its box
    # CLIPPED by the frame, so it measures as very nearly the whole picture
    # and a caller that only asks "is it big enough" happily accepts a
    # close-up of somebody's shoulder. Reported separately so the caller can
    # tell "fills the frame" from "overflows it", which are opposite problems
    # with the same measurement.
    edge = (lo_x <= 0 or lo_y <= 0
            or hi_x >= SIDE - step or hi_y >= SIDE - step)
    # AND WHERE IT SAT, not just how big it was.
    #
    # Correcting the width alone is not enough and the first cut proved it:
    # bounds that are too big are usually also centred somewhere the mesh is
    # not, so tightening the frame fourteen times around the WRONG point threw
    # `risen` clean out of the picture and the next measurement found nothing
    # at all. The middle of what was actually drawn is returned with the size
    # so the camera can be aimed as well as zoomed.
    return (max(hi_x - lo_x, hi_y - lo_y) / float(SIDE),
            (lo_x + hi_x) * 0.5, (lo_y + hi_y) * 0.5, edge)


# WHICH NAMES ARE CREATURES. Filled from `beasts.json` in `main`; see the note
# in `shoot` about why a creature must not be turned like an object.
BEASTS = set()

# AND WHAT POSE EACH ONE STANDS IN. A skeletal mesh's BIND pose is how the rig
# was authored, not how the creature ever looks: this pack rigs its animals
# flat and spread, so photographing the bind pose gave a contact sheet of
# things lying on their sides. The world never shows it either -- it plays an
# idle the instant a beast is drawn. Filled from `beastposes.json`.
POSES = {}


def shoot(w, mesh_path, name):
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        report['errors'].append('%s: no mesh at %s' % (name, mesh_path))
        return
    # BOTH KINDS OF MESH, because the creatures are skeletal and the items are
    # not. `get_bounding_box` exists only on a StaticMesh; a SkeletalMesh
    # answers `get_bounds`, which gives an origin and a half-extent instead of
    # two corners, so it is turned into the same two corners here and nothing
    # below this line has to know which it was handed.
    if hasattr(mesh, 'get_bounding_box'):
        b = mesh.get_bounding_box()
    else:
        sb = mesh.get_bounds()
        o, e = sb.origin, sb.box_extent
        b = unreal.Box(unreal.Vector(o.x - e.x, o.y - e.y, o.z - e.z),
                       unreal.Vector(o.x + e.x, o.y + e.y, o.z + e.z))
    size = b.max - b.min
    mid = (b.max + b.min) * 0.5
    reach = max(size.x, size.y, size.z)
    if reach <= 0:
        report['errors'].append('%s: mesh has no size' % name)
        return

    # TURNED TO SHOW ITS BROAD SIDE.
    #
    # A bow photographed at a fixed angle came out as a stick: it is flat, and
    # the fixed angle happened to look along the flat. A shield would have done
    # the same, and a breastplate. So the item is turned first -- its THINNEST
    # axis is pointed at the camera, which is the one direction that is
    # guaranteed to waste no silhouette -- and every long or flat thing then
    # presents the face that makes it recognisable. A roughly cubic item is
    # unaffected, since for a cube every axis is the thinnest.
    # AND ONLY WHEN IT IS ACTUALLY FLAT. Turning everything this way fixed the
    # bow and broke the helm: a helmet is roughly round, so "the thinnest axis"
    # is arbitrary, and pointing an arbitrary axis at the camera turned it into
    # a disc seen from above. Something within about half of square in every
    # direction is left exactly as it was authored, because for those the
    # three-quarter view is already the readable one.
    #
    # NOR STRAIGHT DOWN THE THIN AXIS. Face-on, a flat thing has no thickness
    # at all and reads as a cut-out; the broad face is turned toward the camera
    # and then tipped twenty-five degrees off it, which is enough to see an
    # edge and know the thing is solid.
    # ---- A CREATURE IS LOOKED AT FROM NEARER ITS OWN HEIGHT ----
    #
    # Thirty degrees down is right for an object lying on a table, which is
    # what every item in this pack is. It is wrong for an animal: a quadruped
    # seen from thirty degrees above foreshortens into a shape with no legs,
    # and the whole contact sheet of creatures read as things lying on their
    # sides. A sheep is recognised from the side, at about its own height.
    #
    # Twelve degrees keeps enough of a downward angle to show the back and
    # stops the silhouette collapsing. The yaw is unchanged so a creature and
    # an item are still lit from the same quarter.
    if name in BEASTS:
        # ---- A CREATURE IS TURNED, BUT ONLY ABOUT ITS OWN UPRIGHT ----
        #
        # Items get their thinnest axis pointed at the camera, which tips them
        # over; that is right for a bow and catastrophic for an animal. So a
        # creature is never tipped -- it keeps the pose it was authored in, and
        # ONLY THE CAMERA MOVES, around the vertical.
        #
        # Which way round is decided by the mesh: a boar is 978 along Y and 331
        # across X, so looking from the X side shows a boar and looking from
        # the Y side shows a snout and a shapeless mass behind it. That is the
        # whole of what was wrong with the first contact sheet -- every animal
        # photographed roughly end-on and read as lying down. The bind pose was
        # standing the entire time: measured on the pig, its body bone sits at
        # z=230 over a front foot at z=10.
        #
        # Twelve degrees down rather than thirty, because an animal is
        # recognised from near its own height.
        broad = 180.0 if size.y >= size.x else 90.0
        look = unreal.Rotator(-12.0, broad, 0.0)
    else:
        look = unreal.Rotator(-30.0, 135.0, 0.0)
    fwd = look.get_forward_vector()
    flat = min(size.x, size.y, size.z) / max(size.x, size.y, size.z, 1e-6)
    faces = None
    # AND A CREATURE IS NEVER TURNED AT ALL.
    #
    # Everything above is a rule about OBJECTS, and it is a good one: a bow is
    # flat and has to be shown its broad side or it is a stick. A creature is
    # not an object. It was authored standing up, facing along its own forward
    # axis, and a goblin is tall and narrow -- so the rule found its thinnest
    # axis, pointed that at the camera, and laid the goblin on its back at
    # forty-five degrees. Recognisable, and plainly wrong in a bestiary.
    #
    # The three-quarter view this camera already stands at is the readable one
    # for anything that stands, which is the same reason a roughly cubic item
    # is left alone below.
    if name in BEASTS:
        turn = unreal.Rotator(0.0, 0.0, 0.0)
    elif flat > 0.40:
        turn = unreal.Rotator(0.0, 0.0, 0.0)
    else:
        thin = min(((size.x, 'x'), (size.y, 'y'), (size.z, 'z')))[1]
        tipped = unreal.MathLibrary.rotate_angle_axis(
            fwd, 25.0, look.get_up_vector())
        turn = {'x': unreal.MathLibrary.make_rot_from_x,
                'y': unreal.MathLibrary.make_rot_from_y,
                'z': unreal.MathLibrary.make_rot_from_z}[thin](tipped)
        # AND FROM THE FRONT OF IT, WHICH IS NOT DECIDED YET.
        #
        # Pointing the thinnest axis at the camera says which way the flat
        # thing lies. It does not say which of its two faces is turned
        # forward, and it had been picking whichever the axis happened to run
        # toward -- so every shield in the pack was photographed from BEHIND,
        # showing the two arm straps and none of the face. Somebody reading
        # their pack saw the back of a shield.
        #
        # The two candidates are kept and settled below, once there is a
        # camera to look through: the face that shows more of the item's
        # colours is the front. A shield's front is oak planks, an iron frame
        # and the band across it; its back is the same metal all over with two
        # straps on it. A bow, which is the other thing this turning was
        # written for, is nearly the same from either side and does not care.
        back = {'x': unreal.MathLibrary.make_rot_from_x,
                'y': unreal.MathLibrary.make_rot_from_y,
                'z': unreal.MathLibrary.make_rot_from_z}[thin](tipped * -1.0)
        faces = [turn, back]

    # THE GRADE, PAINTED ONTO THE METAL AND NOTHING ELSE.
    #
    # See `tiers.py`. The kits name their slots -- `Steel`, `DarkSteel`,
    # `LightGold`, against `LightWood` and `Leather` -- so the parts that
    # change with the grade can be picked out exactly and the haft left as it
    # was. A dynamic instance is used rather than a saved asset because these
    # colours exist for the length of one render and belong to no asset.
    tint = tier_of(name)
    FLAT = unreal.EditorAssetLibrary.load_asset(
        '/Game/Interval/Materials/M_IntervalFlat.M_IntervalFlat')

    here = unreal.Vector(FAR, FAR, FAR)
    # Rotation is about the actor's pivot, not about the mesh's middle, so the
    # middle has to be carried round with it or the item leaves the frame.
    spun = unreal.MathLibrary.greater_greater_vector_rotator(
        unreal.Vector(mid.x, mid.y, mid.z), turn)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, here - spun)
    actor.set_actor_rotation(turn, False)
    # ---- POSED BEFORE IT IS PHOTOGRAPHED ----
    #
    # See the note on POSES. Without this the picture is the bind pose, which
    # for these rigs is the animal flat on its side with its legs out.
    if name in POSES:
        try:
            clip = unreal.EditorAssetLibrary.load_asset(POSES[name])
            comp = actor.get_component_by_class(unreal.SkeletalMeshComponent)
            if clip and comp:
                comp.set_animation_mode(
                    unreal.AnimationMode.ANIMATION_SINGLE_NODE)
                comp.set_animation(clip)
                # ---- AND IT MUST BE TOLD TO ANIMATE OUTSIDE PLAY ----
                #
                # This is the line that matters. A skeletal mesh component
                # does not evaluate animation in the editor unless it is asked
                # to, so setting a clip and a time changed nothing at all and
                # every creature was still photographed in its bind pose.
                #
                # Two earlier attempts reached for `tick_component` and
                # `refresh_bone_transforms`; neither is exposed to Python. The
                # method list is worth reading before guessing a third time.
                comp.set_update_animation_in_editor(True)
                comp.play(False)
                # A LITTLE WAY IN, NOT AT FRAME ZERO. The first frame of an
                # idle is often still the rest pose; a quarter of a second is
                # past it and is not yet anywhere expressive.
                comp.set_position(0.25, False)
        except Exception as e:
            report['errors'].append('%s: pose failed, %s' % (name, str(e)[:70]))

    def place(t):
        # The middle has to be carried round with the rotation or the item
        # leaves the frame; see the note above.
        off = unreal.MathLibrary.greater_greater_vector_rotator(
            unreal.Vector(mid.x, mid.y, mid.z), t)
        actor.set_actor_location(here - off, False, False)
        actor.set_actor_rotation(t, False)
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SceneCapture2D, here, unreal.Rotator(0, 0, 0))
    try:
        # AND ONLY AN ITEM IS TIER-TINTED, NEVER A CREATURE.
        #
        # `tier_of` reads the grade out of the front of the name, and the
        # GREAT SPIDER is not made of great-grade steel: it matched `great-`,
        # came in here, and died on `mesh.static_materials`, which a skeletal
        # mesh does not have. The tinting exists so a quick sword and an iron
        # sword do not render in the same kit colours; a creature has its own
        # skin and nothing here should repaint it.
        if tint and FLAT and hasattr(mesh, 'static_materials'):
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            painted = 0
            for i, slot in enumerate(mesh.static_materials):
                if not is_metal(slot.material_slot_name):
                    continue
                # PARENTED TO THIS PROJECT'S MASTER, NOT TO THE KIT'S.
                #
                # Made from the slot's existing material, the instance is a
                # child of whatever the CC0 pack shipped -- and those have no
                # `DiffuseColor` parameter, so setting one is accepted in
                # silence and changes nothing. Every grade rendered in the
                # kit's own colours and looked almost identical, which is the
                # symptom this whole table exists to cure. `M_IntervalFlat` is
                # the master everything flat-coloured in this window hangs off
                # and it does have the parameter.
                #
                # NOT `mid`: that name is the mesh's bounding-box centre a few
                # lines down, and shadowing it turned the framing maths into an
                # attribute error on a material.
                paint = comp.create_dynamic_material_instance(i, FLAT)
                if paint:
                    paint.set_vector_parameter_value(
                        'DiffuseColor', unreal.LinearColor(tint[0], tint[1],
                                                           tint[2], 1.0))
                    painted += 1
            if painted:
                report['by_slot'].append(name)

        # THE INSTANCE, NOT THE ARCHETYPE. `cam.capture_component2d` hands
        # back the template, and every write to it is refused with "cannot be
        # edited on templates".
        c = cam.get_component_by_class(unreal.SceneCaptureComponent2D)
        c.projection_type = unreal.CameraProjectionMode.ORTHOGRAPHIC
        c.texture_target = target()
        # NOTHING ELSE IS IN FRAME, AND NOT BY FILTERING. A show-only list
        # would be the obvious way to keep the settlement out of the picture,
        # but the orthographic frame here is about as wide as the item is --
        # tens of centimetres -- and it is taken two kilometres above the
        # world. Everything else is outside the frustum by construction.
        c.set_editor_property('capture_every_frame', False)
        c.set_editor_property('capture_on_movement', False)
        c.set_editor_property('always_persist_rendering_state', True)
        # THE THREE-QUARTER VIEW every inventory in this genre uses: from above
        # and off to one side, so a flat thing reads as a thing and not as a
        # line.
        cam.set_actor_rotation(look, False)
        cam.set_actor_location(here - fwd * (reach * 3.0), False, False)

        # FRAMED ON WHAT IS ACTUALLY SEEN, not on the longest edge of the box.
        #
        # A sword's box is as long as the sword, but seen from the corner it
        # lies along the diagonal and covers about seven tenths of that in
        # either screen direction -- so an ortho width of the box's longest
        # edge leaves a third of the icon empty, which for the smallest item in
        # the pack is the difference between a dagger and a speck. The eight
        # corners are projected onto the camera's own right and up vectors and
        # the widest of those decides, which is exact for any shape and any
        # angle.
        right, up = look.get_right_vector(), look.get_up_vector()
        span = 0.0
        for cx in (b.min.x, b.max.x):
            for cy in (b.min.y, b.max.y):
                for cz in (b.min.z, b.max.z):
                    v = unreal.MathLibrary.greater_greater_vector_rotator(
                        unreal.Vector(cx - mid.x, cy - mid.y, cz - mid.z), turn)
                    span = max(span, abs(v.dot(right)), abs(v.dot(up)))
        # A FLOOR OF ONE UNIT IS A FLOOR OF ONE CENTIMETRE, and some of this
        # art is smaller than that. `Helmet1` is authored a hundred times
        # under scale -- parts.py multiplies it by exactly that to hang it on
        # a head -- so its bounding box is about three millimetres, the frame
        # clamped to a centimetre anyway, and the iron helm rendered into a
        # tenth of its own sprite. Measured: 513 lit pixels against 5,150 for
        # the helms beside it.
        #
        # The floor exists so a mesh with no size at all cannot ask for a
        # zero-width camera, and a hundredth of a unit serves that just as
        # well without deciding how big anybody's art has to be.
        c.ortho_width = max(span * 2.0 * 1.08, 0.01)

        # ---- AND THEN CHECKED AGAINST WHAT IT ACTUALLY DREW ----
        #
        # Everything above derives the frame from the mesh's bounds, which is
        # right for a static mesh and can be wildly wrong for a skeletal one;
        # see `fills`. One capture says how much of the frame was really used
        # and the width is corrected from that, so a mesh whose bounds lie
        # ends up framed the same as one whose bounds do not.
        #
        # Only ever TIGHTENS. If the measurement is missing or already close,
        # nothing moves, so this cannot make a good frame worse.
        c.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
        c.show_flag_settings = [
            unreal.EngineShowFlagsSetting(show_flag_name=f, enabled=False)
            for f in ('Lighting', 'Tonemapper', 'Bloom', 'EyeAdaptation',
                      'AntiAliasing', 'Fog', 'AtmosphericFog', 'MotionBlur',
                      'ToneCurve', 'ColorGrading', 'ScreenSpaceReflections',
                      'AmbientOcclusion')]
        # ---- AND THEN CORRECTED AGAINST WHAT IT ACTUALLY DREW ----
        #
        # The frame above comes from the mesh's bounds, which a skeletal mesh
        # reports as its ANIMATED extent: a clip that swings the arms makes a
        # standing figure nearly two metres DEEP, and the camera is framed for
        # a box the creature never occupies. `Tools/bestiary.py` documents the
        # same trap from the other end.
        #
        # So the frame is settled by looking. Photograph, measure the box of
        # what was drawn, aim at its middle and zoom to fill, and repeat until
        # it settles. Three rules keep it honest:
        #
        #   · a CLIPPED measurement means too close, never close enough. The
        #     first cut had no such rule and accepted a close-up of a shoulder
        #     at "eighty-five per cent of the frame", because a thing larger
        #     than the picture fills the picture.
        #   · it stops the moment the fill is in band, so a mesh whose bounds
        #     are honest pays one extra capture and nothing else changes.
        #   · the last good frame is remembered, so a correction that
        #     overshoots cannot leave the item worse than it started.
        WANT, LOW, HIGH = 0.86, 0.55, 0.95
        best = None
        for _ in range(5):
            c.capture_scene()
            c.capture_scene()
            got = fills(w, c.texture_target)
            if got is None:
                break
            used, cx, cy, edge = got
            if not edge and LOW <= used <= HIGH:
                best = None                 # this frame is the good one
                break
            if best is None:
                best = (cam.get_actor_location(), c.ortho_width)
            if edge:
                # Too close: pull back and try again from the middle of what
                # can still be seen.
                c.ortho_width = c.ortho_width * 1.45
            else:
                half = c.ortho_width * 0.5
                dx = ((cx - SIDE * 0.5) / (SIDE * 0.5)) * half
                dy = ((cy - SIDE * 0.5) / (SIDE * 0.5)) * half
                # `cam`, not `c`: the actor moves and `c` is the capture
                # component hanging off it, which has no location to set.
                r_, u_ = look.get_right_vector(), look.get_up_vector()
                at = cam.get_actor_location()
                cam.set_actor_location(unreal.Vector(
                    at.x + r_.x * dx - u_.x * dy,
                    at.y + r_.y * dx - u_.y * dy,
                    at.z + r_.z * dx - u_.z * dy), False, False)
                c.ortho_width = max(c.ortho_width * (used / WANT), 0.01)
            report.setdefault('reframed', {})[name] = round(used, 4)
        if best is not None:
            # It never settled. Put back the frame it started with rather than
            # keep whichever half-corrected guess the loop stopped on.
            where, width = best
            cam.set_actor_location(where, False, False)
            c.ortho_width = width
            report.setdefault('unsettled', []).append(name)

        # ---- THE ALBEDO IS DRAWN UNLIT, NOT READ OUT OF THE GBUFFER ----
        #
        # `SCS_BASE_COLOR` asks the deferred GBuffer for the colour a surface
        # was painted, and it worked for as long as there was an ordinary
        # GBuffer to ask. `r.Substrate=True` replaces it, and the pass started
        # coming back EXACTLY (27,27,27) for every item in the pack --
        # including meshes and materials nobody had touched since the last
        # good render, which is what said it was the renderer and not the art.
        # Lumen was ruled out by putting it back for one render.
        #
        # Unlit is the same picture by another road: with the lighting flag
        # off, what reaches the target is the surface's own colour and nothing
        # else, which is exactly what this pass has always wanted. The
        # tonemapper, the bloom and the eye have to go with it or the colour
        # arrives graded -- and a graded icon is an icon with an hour in it,
        # which is the thing this whole three-pass arrangement exists to
        # refuse.
        unlit = [unreal.EngineShowFlagsSetting(show_flag_name=f, enabled=False)
                 for f in ('Lighting', 'Tonemapper', 'Bloom', 'EyeAdaptation',
                           'AntiAliasing', 'Fog', 'AtmosphericFog',
                           'MotionBlur', 'ToneCurve', 'ColorGrading',
                           'ScreenSpaceReflections', 'AmbientOcclusion')]

        # ---- WHICH OF ITS TWO FACES IS THE FRONT ----
        #
        # Settled by looking, because nothing in a mesh says which side is the
        # front and the axis it happens to lie along is not evidence. Both
        # faces are photographed unlit and the one showing MORE of the item's
        # colours wins: the face of a shield is oak, an iron frame and a band
        # across it, and the back of one is the same metal all over. Two extra
        # draws of one item into a 512-pixel target, and only for things flat
        # enough to have a front at all.
        if faces:
            c.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
            c.show_flag_settings = unlit
            best, most = None, -1.0
            for face in faces:
                place(face)
                c.capture_scene()
                c.capture_scene()
                v = spread(w, c.texture_target)
                if v is not None and v > most:
                    best, most = face, v
            place(best or turn)

        off = unlit
        for src, suffix in ((unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR, 'a'),
                            (unreal.SceneCaptureSource.SCS_NORMAL, 'n'),
                            (unreal.SceneCaptureSource.SCS_DEVICE_DEPTH, 'd')):
            c.capture_source = src
            # Only the albedo wants the world's light taken away; the normal
            # and the depth are geometry and are unaffected either way.
            c.show_flag_settings = off if suffix == 'a' else []
            # CAPTURED TWICE, AND THAT IS NOT SUPERSTITION EITHER. A scene
            # capture renders on the frame it is asked, with whatever the
            # renderer has ready: an actor spawned a few lines above has had no
            # frame yet, so its material's uniforms are not built and it draws
            # with the parent material's DEFAULTS -- which for
            # `M_IntervalFlat` is DiffuseColor 0.5, a flat neutral grey. That
            # is exactly what came out: every sprite rendered since the master
            # was last rebuilt is r == g == b, and the same meshes in the WORLD
            # are correctly coloured, which is what rules out the art, the
            # material instances and the shader compiler all at once.
            #
            # The first call is the one that makes the renderer notice; the
            # second is the picture. It costs one draw of one item into a
            # 512-pixel target.
            c.capture_scene()
            c.capture_scene()
            unreal.RenderingLibrary.export_render_target(
                w, c.texture_target, OUT, '%s.%s.png' % (name, suffix))
            # ---- AND THE ALBEDO IS MEASURED WHERE IT IS TAKEN ----
            #
            # Read back off the render target, not off the PNG afterwards: it
            # is a native call, it costs a few hundred pixels rather than a
            # quarter of a million, and it means `main` can decide to shoot
            # this item again while the camera is still standing there.
            if suffix == 'a':
                report['spread'][name] = spread(w, c.texture_target)
        report['done'].append(name)
    finally:
        unreal.EditorLevelLibrary.destroy_actor(cam)
        unreal.EditorLevelLibrary.destroy_actor(actor)


def main():
    os.makedirs(OUT, exist_ok=True)
    w = world()
    if not w:
        report['errors'].append('no world')
        return
    # ---- THE BASE COLOUR PASS IS A GBUFFER READ ----
    #
    # Every sprite rendered on the 22nd has a coloured albedo and every one
    # rendered tonight came back EXACTLY (27,27,27) -- including meshes and
    # materials that had not been touched in between. That is not a shader
    # waiting to compile; it is the capture's GBuffer read coming back empty,
    # and the thing that changed under it is a project render setting.
    #
    # WHAT WAS RULED OUT, so nobody spends the night on it twice:
    #
    #   the shader compiler   three minutes of warm, then ten, then a
    #                         throwaway render to MAKE the request and ninety
    #                         seconds after it. All three came back neutral.
    #   Lumen                 turned back on for one render. Unchanged.
    #   the art               the same meshes in the WORLD are correctly
    #                         coloured. A forged fishing rod in a citizen's
    #                         hand is brown; its sprite is grey.
    #   the material instances  read back with the right parent, the right
    #                         DiffuseColor and the right expression GUID.
    #   the capture's timing  taken twice, the second after the first. Same.
    #   the materials AT ALL  every slot painted bright red through a dynamic
    #                         instance still captured as (31,31,31). A capture
    #                         that ignores a colour set on the component is not
    #                         a capture with a material problem.
    #
    # What is left is the renderer under it: `r.Substrate=True` replaces the
    # GBuffer outright, and both the base-colour source and the unlit path read
    # that buffer. The depth and the normal passes still come back right, which
    # fits exactly: geometry is fine and colour is gone.
    #
    # Testing that costs a project-wide shader recompile in both directions, so
    # it is not done at three in the morning with somebody asleep. The FORGED
    # sprites are made by `Tools/sprite.py` in the meantime, which draws them
    # from the .obj and the palette with no editor at all.
    have = json.load(open(S + 'items.json'))['have']
    # AND THE CREATURES, which are photographed exactly the way the items are.
    # The handbook draws a picture beside every item and drew none beside any
    # creature, so a reader met twenty-two names and no faces. They are not
    # items and do not belong in `items.json`, so they arrive in a file of
    # their own and are merged here; no creature shares a name with an item,
    # which was checked before this was written rather than hoped for.
    if os.path.exists(S + 'beasts.json'):
        beasts = json.load(open(S + 'beasts.json'))
        have.update(beasts)
        BEASTS.update(beasts)
    if os.path.exists(S + 'beastposes.json'):
        POSES.update(json.load(open(S + 'beastposes.json')))
    # A FILE, NOT AN ENVIRONMENT VARIABLE: this runs inside the editor's own
    # interpreter, which was started hours ago and knows nothing of the shell
    # that asked for the render.
    only = ''
    if os.path.exists(S + 'icons.only'):
        with open(S + 'icons.only') as f:
            only = f.read().strip()
    names = [n for n in only.split(',') if n] if only else sorted(have)

    # ---- A THROWAWAY PASS FIRST, AND IT IS NOT SUPERSTITION ----
    #
    # A material's shader is compiled the first time something ASKS to draw it,
    # and the asking is this render. So the first render of a newly dressed
    # mesh is the request, and it draws with the DEFAULT material while the
    # compiler gets to work: neutral grey, no error, every file written. The
    # note at the top of this file and the one at the top of icons.sh were both
    # written after that cost a day, and the answer in both was "wait longer
    # before rendering" -- which is a guess, and it lost again tonight against
    # ten meshes dressed in the same session, twice, at three minutes and then
    # at ten.
    #
    # Waiting cannot be the answer because nothing had asked yet. So the first
    # pass over the list is thrown away: it exists to make the request. Then a
    # pause, and then the pass that is kept. A second render of a hundred and
    # thirty items costs under a minute and it is not a guess about anybody's
    # machine.
    import time
    for name in names:
        if name in have:
            try:
                shoot(w, have[name], name)
            except Exception:
                pass
    # Everything the throwaway pass recorded goes with it, or the report would
    # count every item twice and the sprites would be the first pass's.
    del report['done'][:]
    del report['errors'][:]
    del report['by_slot'][:]
    report['spread'].clear()
    note('first pass done and thrown away; waiting for the shader compiler')
    time.sleep(90)

    def pass_over(todo):
        for name in todo:
            if name not in have:
                report['errors'].append('%s: no mesh known' % name)
                continue
            try:
                shoot(w, have[name], name)
            except Exception:
                import traceback
                report['errors'].append('%s: %s' % (name, traceback.format_exc()))

    pass_over(names)

    # ---- AND THEN AGAIN, FOR WHATEVER IS STILL NEUTRAL ----
    #
    # The throwaway pass above exists because waiting cannot fix a shader
    # nothing has asked for yet. One request is not enough either: this script
    # is run into an editor that has just been STARTED, so the whole pack's
    # materials are compiling at once, and until that queue drains every item
    # draws with `M_IntervalFlat`'s defaults, which are exactly neutral.
    #
    # Waiting longer has now lost five times -- three minutes, ten, seven, and
    # twice more tonight -- because every one of those was a guess about a
    # particular machine on a particular evening. So it is not a guess any
    # more: every item is measured as it is taken, anything exactly neutral is
    # taken again, and that repeats until nothing is neutral.
    #
    # THE WAIT GROWS AND THE ROUNDS DO NOT GIVE UP EARLY. A first attempt at
    # this stopped as soon as a round mended nothing, on the reasoning that an
    # item which did not come good was simply grey. That is exactly backwards
    # for a compile queue: while it drains, NOTHING comes good, and then all
    # of it does at once. So the only thing that ends this is the pack coming
    # right or the rounds running out.
    # AND THE THINGS WHOSE ART IS HONESTLY NEUTRAL ARE NOT CHASED. `matte.py`
    # already knows the sheep's mesh ships materials named `Black` and `White`
    # and lets it through; this loop did not, so every render spent eight
    # rounds and eighteen minutes re-photographing a sheep that was right the
    # first time. The two lists must agree: see TRULY_NEUTRAL in matte.py.
    HONEST = {'sheep'}
    for attempt in range(8):
        grey = sorted(n for n, v in report['spread'].items()
                      if v is not None and v < 1 and n not in HONEST)
        if not grey:
            if attempt:
                note('came right on round %d' % attempt)
            break
        wait = 30 * (attempt + 1)
        note('%d still exactly neutral; waiting %ds and taking them again (%s)'
             % (len(grey), wait, ', '.join(grey[:6])))
        time.sleep(wait)
        for n in grey:
            report['spread'].pop(n, None)
        pass_over(grey)
    else:
        note('gave up with %d still neutral' % len(
            [n for n, v in report['spread'].items()
             if v is not None and v < 1]))
    with open(S + 'icons.json', 'w') as f:
        json.dump(report, f, indent=1)
    # Next to the passes, because `matte.py` reads it from there and the two
    # belong to the same render.
    with open(os.path.join(OUT, 'by_slot.json'), 'w') as f:
        json.dump(report['by_slot'], f)
    note('DONE %d rendered, %d errors' % (len(report['done']), len(report['errors'])))


main()
