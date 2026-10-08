# Imports the .wav files beside the Content folder as SoundWave assets.
# There is no sound-import tool on the MCP server and the editor does not
# watch the content directory, so this runs inside the editor's own Python.
import os
import unreal

# THE SOURCES LIVE OUTSIDE Content/, ON PURPOSE.
#
# They used to sit in Content/Interval/Audio beside the imported assets, which
# is tidy and is a trap: the editor watches the content directory, so every
# time the beds were re-synthesised the next editor to start opened a "changes
# to source content files have been detected, import them?" dialog. Under
# automation that is a box nobody is there to click, which is the same class
# of fault as the auto-save restore prompt ue.sh deletes.
SRC = os.path.abspath(unreal.Paths.project_dir() + 'Audio')
tasks = []
for name in sorted(os.listdir(SRC)):
    if not name.endswith('.wav'):
        continue
    t = unreal.AssetImportTask()
    t.filename = os.path.join(SRC, name)
    t.destination_path = '/Game/Interval/Audio'
    t.destination_name = os.path.splitext(name)[0].replace('-', '_')
    t.automated = True
    t.replace_existing = True
    t.save = True
    tasks.append(t)

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

# Everything here is either a bed or a piece, and both want to loop --
# a theme that stops dead leaves the world sounding switched off.
lib = unreal.EditorAssetLibrary
made = []
for t in tasks:
    path = '/Game/Interval/Audio/' + t.destination_name
    a = lib.load_asset(path)
    if a is None:
        print('MISSING', path)
        continue
    a.set_editor_property('looping', t.destination_name.startswith('amb_'))
    lib.save_asset(path)
    made.append(t.destination_name)
print('IMPORTED', len(made), ' '.join(made))
