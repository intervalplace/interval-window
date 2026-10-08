# SET `bUsedWithNanite` ON EVERY MATERIAL THIS WORLD DRAWS.
#
#   pyrun.sh nanite_flags.py
#
# WHAT IT FIXES, AND WHY IT ONLY SHOWS IN A PACKAGE. A material applied to a
# Nanite mesh must carry the Nanite usage flag or the renderer has no shader
# for that combination. In the EDITOR this is invisible: Unreal notices, sets
# the flag on the spot, compiles the permutation, and carries on -- and because
# nothing saves the asset, it does the same thing again at the next launch.
# The log says so in as many words:
#
#   Material .../MP_Leaves missing usage flag Nanite! Default Material will be
#   used in game. The material instance will recompile every editor launch
#   until resaved.
#
# A packaged client has no shader compiler. There is nothing to fall back on
# but the Default Material, so the mesh renders flat grey -- which is what the
# first launch of the Mac client showed across the terrain, the kits and the
# props: forty-seven materials, all of them silently replaced.
#
# THE FLAG LIVES ON THE MATERIAL, NOT THE INSTANCE. A material instance asks
# its parent, so setting it on the instances does nothing at all; this walks to
# the base material of whatever it finds and sets it there.
#
# IT COSTS A SHADER PERMUTATION PER MATERIAL AND NOTHING ELSE. There is no
# runtime price for a flag that is set and unused, which is why this does not
# try to work out which meshes are Nanite: being wrong in that direction costs
# cook time, and being wrong in the other costs the whole look of the world.
import unreal, traceback
out = []

ROOT = '/Game/Interval'

lib = unreal.EditorAssetLibrary
found = lib.list_assets(ROOT, recursive=True, include_folder=False)
bases, touched, already = set(), [], 0

try:
    pass
except Exception:
    pass
for path in found:
    asset = lib.load_asset(path.split('.')[0])
    if asset is None:
        continue
    base = None
    if isinstance(asset, unreal.MaterialInstance):
        # walk up to the material that actually owns the flag
        parent = asset.get_editor_property('parent')
        while isinstance(parent, unreal.MaterialInstance):
            parent = parent.get_editor_property('parent')
        base = parent if isinstance(parent, unreal.Material) else None
    elif isinstance(asset, unreal.Material):
        base = asset
    if base is None:
        continue
    bases.add(base.get_path_name())

# ---- READING THE FLAG TELLS YOU NOTHING. SAVE REGARDLESS. ----
#
# The first version of this skipped any material that already reported
# `used_with_nanite`, and every one of the hundred and thirty-seven did -- while
# the packaged client went on drawing forty-seven of them as the Default
# Material. The editor SETS the flag on load, in memory, and that is the whole
# content of the warning's last clause: "will recompile every editor launch
# UNTIL RESAVED". So the property is true the moment you can ask about it, and
# it is false on disk, which is the only place a cook reads.
#
# There is nothing to test, then. Set it and save it, every time.
for p in sorted(bases):
    m = lib.load_asset(p.split('.')[0])
    if m is None:
        continue
    try:
        m.set_editor_property('used_with_nanite', True)
        if lib.save_asset(p.split('.')[0], only_if_is_dirty=False):
            touched.append(p.split('/')[-1])
        else:
            already += 1
    except Exception as e:
        out.append('could not set the flag on %s: %s' % (p, e))

out.append('%d base materials under %s; %d refused the save, %d written to disk'
           % (len(bases), ROOT, already, len(touched)))
out += ['  set ' + t for t in touched]
open('/tmp/nanite.txt', 'w').write('\n'.join(out))
