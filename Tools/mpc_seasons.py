# ADD A PARAMETER TO THE WEATHER COLLECTION, which MCP cannot do.
#
#   pyrun.sh mpc_seasons.py
#
# `make_mpc.py` builds MPC_IntervalSky over MCP and that works for CREATING it,
# because setting an empty array to N elements is a size change with nothing to
# be ambiguous about. Growing one that already has five is refused:
#
#   ArrayAdd: elements changed alongside the size change; insertion points are
#   ambiguous.
#
# and it is refused whatever you try, including padding with exact copies of
# the last element. There is no collection-parameter tool on the material
# toolset either. So this is the editor's own interpreter, which is the same
# escape hatch `import_forged.py` uses for the same reason.
#
# NEVER DELETE AND RE-CREATE THE COLLECTION. A material does not reference a
# collection parameter by name, it stores the parameter's GUID, and a fresh
# collection mints fresh ones -- so recreating this at the same path silently
# unbinds every material that reads the weather, with no error and no warning,
# and the ground quietly stops knowing whether it is raining. make_mpc.py has
# the scar. This APPENDS and never touches what is already there.
import unreal

PATH = '/Game/Interval/MPC_IntervalSky'

# The three the seasons need. The year turns in twenty-eight days off the
# constitutional day index alone, so every window over this world agrees on
# the calendar without the engine having a word for a season.
WANT = [('Autumn', 0.0), ('Winter', 0.0), ('Spring', 0.0)]

coll = unreal.EditorAssetLibrary.load_asset(PATH)
if not coll:
    raise SystemExit('no collection at ' + PATH)

scalars = list(coll.get_editor_property('scalar_parameters'))
have = {str(p.get_editor_property('parameter_name')) for p in scalars}
added = []
for name, default in WANT:
    if name in have:
        continue
    p = unreal.CollectionScalarParameter()
    p.set_editor_property('parameter_name', name)
    p.set_editor_property('default_value', default)
    # THE ID IS THE ENGINE'S TO MINT. `Id` is protected and cannot be read or
    # written from Python at all -- trying it throws. A fresh
    # CollectionScalarParameter carries a new guid of its own, which is what
    # binds a material to it, and the only thing that must not happen is
    # RE-minting the ids of the five that already exist. Appending never
    # touches those, which is the whole reason this appends.
    scalars.append(p)
    added.append(name)

if added:
    coll.set_editor_property('scalar_parameters', scalars)
    unreal.EditorAssetLibrary.save_asset(PATH)

names = [str(p.get_editor_property('parameter_name'))
         for p in coll.get_editor_property('scalar_parameters')]
print('DONE mpc_seasons: added %s; collection holds %s'
      % (', '.join(added) if added else 'nothing (already there)', ', '.join(names)))
