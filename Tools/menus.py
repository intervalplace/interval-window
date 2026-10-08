# EVERY MENU IN REACH, READ RATHER THAN CLICKED.
#
# The standing rule for this window is that a right-click lists only what is
# actually possible right now -- not every option the world defines, left for
# the engine to refuse. Three classes of impossible line have been closed by
# finding them one at a time, with a cursor, which is slow and only ever looks
# at whatever happened to be under the mouse.
#
# `TargetsAt` and `OptionsFor` are both BlueprintPure, so the menu for any tile
# can be ASKED for. This sweeps the tiles around the citizen and prints what
# each one would offer. Nothing is filed and nothing is clicked: it is the same
# function the menu is built from, read out loud.
#
# It is not a replacement for clicking. A menu that is correct and opens
# off-screen is still broken, and only a real cursor finds that. This is for
# the other half: whether the LINES are right, over a whole town at once.
#
#   exec py .../menus.py          the tiles within eight of the citizen
import json, os, unreal

S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
     'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')
OUT = S + 'menus.json'
# FAR ENOUGH TO COVER A TOWN. The ground answers "walk here" on every tile and
# says nothing, so it is counted and not listed; what is worth reading is the
# NODES -- a town's wells, hearths, vaults, stalls, plots and keepers -- and
# there are a few dozen of those in a couple of thousand tiles.
REACH = int(os.environ.get('MENUS_REACH', '22'))


def world():
    es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    return es.get_game_world() or es.get_editor_world()


def hand():
    w = world()
    if not w:
        return None
    found = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.IntervalHand)
    return found[0] if found else None


def main():
    h = hand()
    if not h:
        unreal.log_warning('MENUS no hand: is PIE up?')
        return
    # WHERE TO SWEEP FROM, written in by whoever asked. The bridge knows where
    # the citizen is and answers over HTTP in one line; reaching the same fact
    # from inside the editor means finding a game-instance subsystem through a
    # world that Python hands back without one, which is three wrong turns for
    # a number the shell already has.
    at = S + 'menus.at'
    if not os.path.exists(at):
        unreal.log_warning('MENUS no menus.at: write "x y" into it first')
        return
    cx, cy = (int(v) for v in open(at).read().split()[:2])
    report = {'at': [cx, cy], 'tiles': [], 'reach': REACH}
    seen = 0
    for dy in range(-REACH, REACH + 1):
        for dx in range(-REACH, REACH + 1):
            tx, ty = cx + dx, cy + dy
            try:
                targets = h.targets_at(tx, ty)
            except Exception as exc:
                report.setdefault('errors', []).append('%d,%d: %s' % (tx, ty, exc))
                continue
            for t in targets:
                if str(t.kind).endswith('GROUND: 0>'):
                    report['ground'] = report.get('ground', 0) + 1
                    continue
                try:
                    opts = h.options_for(t)
                except Exception as exc:
                    report.setdefault('errors', []).append(
                        '%d,%d %s: %s' % (tx, ty, t.name, exc))
                    continue
                report['tiles'].append({
                    'x': tx, 'y': ty,
                    'kind': str(t.kind).split('.')[-1],
                    'name': str(t.name),
                    'sub': str(t.sub),
                    'lines': [str(o.label) for o in opts],
                    'verbs': [str(o.verb) for o in opts],
                })
                seen += 1
    with open(OUT, 'w') as f:
        json.dump(report, f, indent=1)
    unreal.log('MENUS %d things in reach of %d,%d -> %s' % (seen, cx, cy, OUT))


main()
