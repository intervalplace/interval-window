# The posed copies, as static meshes, for the handbook's pictures.
#
# `Tools/posebake.py` runs in Blender, applies each creature's own idle to its
# own rig, and writes the result to Art/Posed as an OBJ with the armature baked
# into the vertices. This brings those in.
#
# WHY A SECOND COPY EXISTS AT ALL. A skeletal mesh component in the Unreal
# editor never evaluates its animation, so the icon renderer photographs the
# bind pose and the bestiary went to print with a goblin, a troll and an imp
# standing in a T-pose. Five ways of asking were tried and the bone did not
# move once; the note is in Tools/icons.py. The world is unaffected and goes on
# drawing the rigged mesh and animating it properly.
#
# Everything about the import is the forged one's: static, Z-up already so
# `convert_scene` is off, and `import_materials` FALSE so the importer does not
# make its own instances beside the ones dress_wild.py already built.
import os, json, unreal

ART = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'Posed'))
DEST = '/Game/Interval/Posed'
WILD = '/Game/Interval/Wild/'
OUT = (r"/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/"
       r"d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/posed.json")

# word -> the Wild folder its materials were built under, so a slot called
# `Orc_Main` can find `MW_goblin_c_Orc_Main`. Kept here rather than guessed
# from the word, because the folder is the SOURCE's name and the word is ours.
FROM = {
    'goblin': 'goblin_c',
    'troll': 'ogre',
    'scree-imp': 'monster_a',
}

# ---- AND THE PEOPLE, WHOSE SLOTS ARE NAMED BY THE SOURCE AND NOT BY US ----
#
# The five corpses are a bare body plus an outfit, and both halves come in
# naming their materials `MI_<something>` -- the names Quaternius shipped.
# What Unreal is wearing is `MP_<something>`, built by the import that made the
# people in the first place. The rename is one to one, except that the BODY of
# a corpse wears the drained copies in Beasts/Risen rather than a living
# citizen's skin, which is the whole point of those three.
PEOPLE = '/Game/Interval/Universal/People/'
# The drained copies live in Universal/Base beside the body they are a copy
# OF, not in Beasts/Risen beside the mesh that wears them. Looked up rather
# than assumed, after assuming it once and binding nothing.
RISEN = '/Game/Interval/Universal/Base/'
SLOT = {
    'MI_Hair_1': RISEN + 'MP_Dead_Hair',
    'MI_Hair_2': RISEN + 'MP_Dead_Hair',
    'MI_Eyes': RISEN + 'MP_Dead_Eyes',
    'MI_Superhero_Male': RISEN + 'MP_Dead_Male',
    'MI_Superhero_Female': RISEN + 'MP_Dead_Female',
    'MI_Peasant': PEOPLE + 'MP_Peasant',
    'MI_Ranger': PEOPLE + 'MP_Ranger',
    'MI_Knight': PEOPLE + 'MP_Knight',
    'MI_Noble': PEOPLE + 'MP_Noble',
    'MI_Wizard': PEOPLE + 'MP_Wizard',
    'MI_Regular_Male': PEOPLE + 'MP_Regular_Male',
    'MI_Regular_Female': PEOPLE + 'MP_Regular_Female',
}

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'errors': [], 'meshes': []}


def options():
    ui = unreal.FbxImportUI()
    ui.set_editor_property('import_mesh', True)
    ui.set_editor_property('import_as_skeletal', False)
    ui.set_editor_property('import_animations', False)
    ui.set_editor_property('import_materials', False)
    ui.set_editor_property('import_textures', False)
    ui.set_editor_property('mesh_type_to_import',
                           unreal.FBXImportType.FBXIT_STATIC_MESH)
    sm = ui.get_editor_property('static_mesh_import_data')
    sm.set_editor_property('combine_meshes', True)
    sm.set_editor_property('convert_scene', False)
    sm.set_editor_property('generate_lightmap_u_vs', False)
    return ui


tasks = []
if not os.path.isdir(ART):
    report['errors'].append('no Art/Posed -- run posebake.py in Blender first')
else:
    for f in sorted(os.listdir(ART)):
        if not f.lower().endswith('.obj'):
            continue
        t = unreal.AssetImportTask()
        t.set_editor_property('filename', os.path.join(ART, f))
        t.set_editor_property('destination_path', DEST)
        t.set_editor_property('destination_name', os.path.splitext(f)[0])
        t.set_editor_property('automated', True)
        t.set_editor_property('replace_existing', True)
        t.set_editor_property('save', True)
        t.set_editor_property('options', options())
        tasks.append(t)
    tools.import_asset_tasks(tasks)

# ---- AND DRESSED FROM THE INSTANCES THAT ALREADY EXIST ----
#
# dress_wild.py made one material instance per slot of the rigged mesh and
# named it `MW_<source>_<slot>`. The baked copy keeps its slot names, which is
# the whole reason posebake.py is careful not to rename them, so each slot can
# find the instance the living creature is already wearing. The posed copy and
# the rigged one are then the same colour by construction rather than by
# somebody keeping two tables in step.
for p in sorted(lib.list_assets(DEST, recursive=True, include_folder=False)):
    data = lib.find_asset_data(p)
    if str(data.asset_class_path.asset_name) != 'StaticMesh':
        continue
    mesh = lib.load_asset(p)
    word = p.rsplit('/', 1)[-1].split('.')[0]
    stem = FROM.get(word)
    slots = [str(x.material_slot_name) for x in mesh.static_materials]
    bound, lost = 0, []
    if stem is None:
        # a person: the slot names are the source's own, and SLOT says what
        # each one is wearing here.
        for i, slot in enumerate(slots):
            # BLENDER NUMBERS A NAME IT HAS SEEN BEFORE. The body and the
            # outfit are two files and both carry an `MI_Eyes`, so the second
            # arrives as `MI_Eyes.001` and matches nothing.
            want = SLOT.get(slot.split('.')[0])
            mi = lib.load_asset('%s.%s' % (want, want.rsplit('/', 1)[-1])) if want else None
            if mi:
                mesh.set_material(i, mi)
                bound += 1
            else:
                lost.append(slot)
        if bound:
            lib.save_asset(p, False)
    else:
        for i, slot in enumerate(slots):
            # A DOT IS NOT A DOT BY THE TIME IT IS AN ASSET NAME. The ogre's
            # one slot is called `Atlas.001` and dress_wild.py's instance for
            # it is `MW_ogre_Atlas_001`, because Unreal will not have a dot in
            # an asset name. Matching the slot verbatim finds nothing.
            name = 'MW_%s_%s' % (stem, slot.replace('.', '_'))
            path = '%s%s/%s.%s' % (WILD, stem, name, name)
            mi = lib.load_asset(path)
            if mi:
                mesh.set_material(i, mi)
                bound += 1
            else:
                lost.append(name)
        if bound:
            lib.save_asset(p, False)
    b = mesh.get_bounding_box()
    s = b.max - b.min
    row = {'path': p, 'name': word,
           'cm': [round(s.x, 1), round(s.y, 1), round(s.z, 1)],
           'slots': slots, 'bound': bound}
    if lost:
        row['unmatched'] = lost
        report['errors'].append('%s: no instance for %s' % (word, ', '.join(lost)))
    report['meshes'].append(row)

json.dump(report, open(OUT, 'w'), indent=1)
print('DONE posed: %d mesh(es), %d error(s)'
      % (len(report['meshes']), len(report['errors'])))
for m in report['meshes']:
    print('   %-12s %-22s %d/%d slots bound'
          % (m['name'], 'x'.join(str(v) for v in m['cm']),
             m['bound'], len(m['slots'])))
for e in report['errors']:
    print('   ! ' + e)
