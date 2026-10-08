# The inventory sprites, as textures the pack can draw.
#
# Settings matter more here than for any other texture in this project, and
# all three of these are wrong by default:
#
#   UserInterface2D compression, because the default (DXT) is block
#   compression built for surfaces seen at an angle across a room. On a
#   thirty-two pixel icon with a hard silhouette it eats the edge and puts
#   coloured mush round every blade.
#
#   NO MIPMAPS, because an icon is drawn at one size and a mip chain on a
#   sprite this small is both waste and a source of blurring when the interface
#   is scaled.
#
#   sRGB ON: `matte.py` encodes once at the end, so what is in these files is
#   the colour as it should appear, not light.
import json, os, unreal

ICONS = os.path.abspath(os.path.join(unreal.Paths.project_dir(), 'Art', 'Icons'))
DEST = '/Game/Interval/Icons'
S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
     'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary
report = {'made': [], 'errors': []}

tasks = []
for f in sorted(os.listdir(ICONS)):
    if not f.endswith('.png'):
        continue
    t = unreal.AssetImportTask()
    t.set_editor_property('filename', os.path.join(ICONS, f))
    t.set_editor_property('destination_path', DEST)
    # Asset names take no hyphens; the pack turns an item name into this
    # spelling to find its sprite -- see `IconFor` in IntervalHud.cpp.
    t.set_editor_property('destination_name', f[:-4].replace('-', '_'))
    t.set_editor_property('automated', True)
    t.set_editor_property('replace_existing', True)
    t.set_editor_property('save', True)
    tasks.append(t)
tools.import_asset_tasks(tasks)

for p in sorted(lib.list_assets(DEST, recursive=False, include_folder=False)):
    tex = lib.load_asset(p)
    if not isinstance(tex, unreal.Texture2D):
        continue
    try:
        tex.set_editor_property('compression_settings',
                                unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        # MIPMAPS ON, and this was wrong the other way round for a while.
        #
        # The reasoning for turning them off was that an icon is drawn at one
        # size, so a mip chain is waste. It is not drawn at one size: the
        # sprites are rendered at 128 and the pack draws them at 44, and the
        # cursor is rendered at 96 and drawn at 30. Sampling a 96-pixel blade
        # with a dark outline at a third of its size, with no mip to average
        # into, takes four texels and the outline wins -- the gold cursor came
        # out a black smudge and every thin item in the pack came out faint.
        # A mip chain IS the average, and is what makes a downscaled sprite
        # look like the thing instead of like a screen door.
        tex.set_editor_property('mip_gen_settings',
                                unreal.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE)
        tex.set_editor_property('srgb', True)
        tex.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
        lib.save_asset(p)
        report['made'].append(p.rsplit('/', 1)[-1])
    except Exception as exc:
        report['errors'].append('%s: %s' % (p, exc))

with open(S + 'icons_import.json', 'w') as f:
    json.dump(report, f, indent=1)
unreal.log('ICON IMPORT DONE: %d textures, %d errors'
           % (len(report['made']), len(report['errors'])))
