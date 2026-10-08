# What the window draws, and how many levels of detail it has to draw it with.
#
# THERE IS NO LOD TOOL ON THE MCP SURFACE, so this runs inside the editor's own
# interpreter like the importers do.
#
# Run with no argument it AUDITS and changes nothing. Run with `build` it
# generates the missing levels. Auditing first is not caution for its own sake:
# a mesh that already has levels was given them by its author and is usually
# better than anything generated, and overwriting those is a silent downgrade.
import json, os, sys
import unreal

# THE COMMANDLET SWALLOWS print(). Every result this project's editor-Python
# produces is written to a file for the same reason -- see whereshour.py.
REPORT = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
          'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/lods.json')
said = []


def say(line):
    said.append(line)
    unreal.log(line)

lib = unreal.EditorAssetLibrary

# WAIT FOR THE REGISTRY. In a cold commandlet nothing has been scanned yet, so
# listing a folder answers with an empty list and every mesh in the project is
# skipped in silence -- which reads exactly like a project that contains no
# static meshes. The importer scripts never hit this because they list assets
# they have just created, which the registry already knows about.
ARG = unreal.AssetRegistryHelpers.get_asset_registry()
# THE WHOLE MOUNT, not the folder. Scanning '/Game/Interval' alone answered
# with nothing; scanning '/Game' answers with all nine hundred and ninety-nine.
ARG.scan_paths_synchronous(['/Game'], force_rescan=True)
ARG.wait_for_completion()

# THE SUBSYSTEM IF THERE IS ONE, AND THERE IS ONLY ONE IN A LIVE EDITOR.
#
# `-run=pythonscript` does not create editor subsystems, so in a commandlet
# this answers None -- and the deprecated library it points at has no working
# `set_lods` either: it returns -1 for every mesh, reports no reason, and the
# script cheerfully counts a hundred and twenty-six successes that never
# happened. So this script is run through the LIVE editor instead, by giving
# the console `py` the path to it at startup:
#
#   LODS_BUILD=1 UE_EXEC='py .../lods.py' ue.sh
SMS = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
trouble = []

FOLDERS = ['/Game/Interval']

# What a level of detail costs at the distance this window watches from. The
# camera sits about eighteen metres out; a prop is a few hundred triangles
# there and a few dozen at the far edge of the streamed window.
REDUCTIONS = [1.0, 0.55, 0.28, 0.12]
# SCREEN SIZE IS A FRACTION OF THE VIEWPORT HEIGHT, AND THE OLD LADDER ASKED
# FOR THE IMPOSSIBLE.
#
# It was [1.0, 0.42, 0.16, 0.05] -- LOD0 only once a mesh fills the WHOLE
# SCREEN. Nothing in a window that looks straight down ever does. The camera
# sits 1150 back and 1380 up (WatchReach/WatchRise), which is 18m, and with a
# 58.7-degree vertical field of view that puts a 1.6m hedge at 0.133 and a
# 4.3m tree at 0.257. So every hedge on the island drew at LOD3 -- 108
# triangles out of 899 -- and the tree beside it at LOD2, which is exactly
# what a photograph of the goblin pound showed.
#
# This ladder is built from that arithmetic instead: LOD0 out to about twenty
# metres, which is the citizen's own surroundings, and down from there.
SCREEN     = [1.0, 0.10, 0.05, 0.02]

# A MARKER FILE, NOT AN ARGUMENT AND NOT AN ENVIRONMENT VARIABLE.
#
# The commandlet passes nothing after -script through to sys.argv, and the
# environment does not survive the hop into an editor launched by a script
# either. Both failures look identical from outside: a second audit, reporting
# the same meshes still bare, which reads as a build that did nothing. A file
# beside the report is the one channel that certainly crosses.
MARK = REPORT.replace('lods.json', 'lods.build')
build = os.path.exists(MARK)

rows = []
for folder in FOLDERS:
    for data in ARG.get_assets_by_path(folder, recursive=True):
        if str(data.asset_class_path.asset_name) != 'StaticMesh':
            continue
        path = str(data.package_name)
        mesh = lib.load_asset(path)
        if not isinstance(mesh, unreal.StaticMesh):
            continue
        # THE SUBSYSTEM, not the deprecated library -- and NOT inside a bare
        # `except: continue`. The first version swallowed the exception from a
        # function that no longer exists, skipped all nine hundred meshes one
        # by one, and reported a project with no static meshes in it. An audit
        # that cannot fail loudly is not an audit.
        # ASKED OF THE MESH ITSELF. Both the editor subsystem and the
        # deprecated library turned out to be the wrong door here -- the
        # subsystem does not exist in a commandlet and the library has no
        # triangle count at all. The object has both.
        # ASKED OF THE MESH ITSELF, which answers both without any subsystem.
        try:
            lods = mesh.get_num_lods()
            tris = mesh.get_num_triangles(0)
        except Exception as e:
            if len(trouble) < 3:
                trouble.append('%s: %s' % (path.split('/')[-1], e))
            continue
        rows.append((path, lods, tris))

rows.sort(key=lambda r: -r[2])
bare = [r for r in rows if r[1] <= 1]
for t in trouble:
    say('   TROUBLE %s' % t)
say('MESHES %d  with levels %d  bare %d  triangles at LOD0 %d'
    % (len(rows), len(rows) - len(bare), len(bare), sum(r[2] for r in rows)))
for path, lods, tris in bare[:24]:
    say('   bare %7d  %s' % (tris, path.split('/')[-1]))
for path, lods, tris in [r for r in rows if r[1] > 1][:6]:
    say('   has%d %7d  %s' % (lods, tris, path.split('/')[-1]))

# ---------------------------------------------------------------------------
# AND RETUNING THE ONES THAT ALREADY HAVE LEVELS.
#
# A mesh that arrived with its author's levels keeps them -- see the note at
# the top -- but it does NOT get to keep their screen sizes, because those were
# chosen for a camera standing on the ground and this one hangs eighteen metres
# over it. Retuning is separate from building for that reason: the geometry is
# the author's and the distances are ours.
#
# `set_lod_thresholds` OVER MCP DID NOT SURVIVE A RESTART. It wrote the values
# and they read back correctly, and after the editor came up again they were
# empty -- because `bAutoComputeLODScreenSize` was still true and the mesh
# recomputed them on load. The flag is editor-only data and is not on the
# reflected property surface, so it cannot be reached from outside at all.
# That is the whole reason this pass lives in here with the builder.
RETUNE = os.path.exists(REPORT.replace('lods.json', 'lods.retune'))
if RETUNE:
    fixed = 0
    still = []
    refused = []
    for path, lods, tris in rows:
        if lods <= 1:
            continue
        mesh = lib.load_asset(path)
        want = SCREEN[:lods] if lods <= len(SCREEN) else \
            SCREEN + [SCREEN[-1] / (2 ** (i + 1)) for i in range(lods - len(SCREEN))]
        # THE SUBSYSTEM, and only the subsystem.
        #
        # `UStaticMesh` itself has no setter for this at all -- no
        # `set_lod_screen_size`, and `auto_compute_lod_screen_size` is not on
        # its property surface either, so both the obvious routes answer with
        # "failed to find property". `StaticMeshEditorSubsystem` has
        # `set_lod_screen_sizes`, which writes the whole ladder and clears the
        # auto-compute flag with it. The mesh can be ASKED whether it is still
        # auto-computing (`is_lod_screen_size_auto_computed`), which is how
        # this pass proves it worked rather than assuming.
        try:
            SMS.set_lod_screen_sizes(mesh, want)
            # `only_if_is_dirty` DEFAULTS TO TRUE, and this is the second time
            # tonight that a write "succeeded" and never reached the disk. The
            # subsystem changes the mesh without marking its package dirty, so
            # the default save looked at a clean package and did nothing -- and
            # the values read back correctly until the editor restarted, when
            # the author's original ladder came back. Save regardless.
            mesh.modify()
            lib.save_asset(path, only_if_is_dirty=False)
            if mesh.is_lod_screen_size_auto_computed():
                still.append(path.split('/')[-1])
            fixed += 1
        except Exception as e:
            if len(refused) < 3:
                refused.append('%s %s' % (path.split('/')[-1], str(e)[:70]))
    for r in refused:
        say('   REFUSED %s' % r)
    if still:
        say('   STILL AUTO-COMPUTED (%d): %s' % (len(still), ' '.join(still[:6])))
    say('DONE retuned screen sizes on %d meshes to %s' % (fixed, SCREEN))
    json.dump(said, open(REPORT, 'w'), indent=1)
    raise SystemExit(0)

if not build:
    say('DONE audit only -- run with `build` to generate the missing levels')
    json.dump(said, open(REPORT, 'w'), indent=1)
    raise SystemExit(0)

# ONLY THE ONES WORTH IT. Generating three levels for a forty-triangle cube
# costs more in asset size and build time than it can ever save, and the
# window is full of engine primitives.
made = 0
for path, lods, tris in bare:
    if tris < 400:
        continue
    mesh = lib.load_asset(path)
    opts = unreal.StaticMeshReductionOptions()
    settings = []
    # FROM LOD0, NOT FROM LOD1. The settings array describes every level
    # including the base one, so the first entry has to be the mesh at full
    # size -- handing it three entries starting at 55% quietly halves the
    # model everyone sees close up.
    for i in range(0, 4):
        r = unreal.StaticMeshReductionSettings()
        r.percent_triangles = REDUCTIONS[i]
        r.screen_size = SCREEN[i]
        settings.append(r)
    opts.reduction_settings = settings
    opts.auto_compute_lod_screen_size = False
    try:
        got = SMS.set_lods(mesh, opts)
        if got is not None and got < 0:
            say('   REFUSED %s' % path.split('/')[-1])
            continue
        lib.save_asset(path)
        made += 1
    except Exception as e:
        say('   FAILED %s %s' % (path.split('/')[-1], e))
say('DONE built levels for %d meshes (subsystem %s)'
    % (made, 'yes' if SMS else 'NO -- nothing was built'))
json.dump(said, open(REPORT, 'w'), indent=1)
