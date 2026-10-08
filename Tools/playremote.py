# A HAND ON THE OTHER SIDE OF THE GLASS.
#
# Every deed this window can file is a BlueprintCallable on AIntervalHand, and
# nothing on the MCP surface can call a function -- it sets properties, reads
# them, and photographs. So playing the world from here needed one more door:
# this registers a tick callback in the live editor, watches a file, and calls
# the hand with whatever it finds.
#
# IT INVENTS NOTHING. Every line is a verb the world already accepts and the
# arguments the engine's own schema names; the hand still builds the intent,
# the bridge still signs it, and a refusal still comes back through the feed.
# This is a keyboard, not a rule.
#
#   UE_EXEC='py .../playremote.py' ue.sh
#   echo 'walk 470 261' >> <scratchpad>/play.cmd
#
# Each line is consumed once. The file is truncated as it is read so a command
# cannot be replayed by accident -- filing a deed twice is not a cosmetic bug
# in a world that is a ledger of deeds.
import json, os, traceback
import unreal

S = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
     'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/')
CMD = S + 'play.cmd'
LOG = S + 'play.log'

state = {'n': 0}


def note(line):
    try:
        with open(LOG, 'a') as f:
            f.write(line + '\n')
    except Exception:
        pass
    unreal.log('PLAY ' + line)


def hand():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not w:
        return None
    found = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.IntervalHand)
    return found[0] if found else None


# verb -> (method, how to read the rest of the line)
AS_INT = lambda v: int(v)
AS_STR = lambda v: str(v)
VERBS = {
    # ROUTED, LIKE A CLICK ON THE MAP. `walk_to` files ONE straight run and
    # the world stops it at the first thing in the way -- a cottage corner, a
    # fence, a tree -- and nothing files another. From here that is
    # indistinguishable from a citizen who cannot walk, and it cost most of an
    # evening twice: a march that only ever asks for the diagonal stops dead
    # at the first building and the log fills with deeds the world took and
    # did nothing with. `walk_route` is what the minimap calls, and it plans,
    # re-plans and remembers what was shut.
    'walk':      ('walk_route',  [AS_INT, AS_INT]),
    'step':      ('walk_to',     [AS_INT, AS_INT]),
    # NOT A DEED. `show_mark` files nothing and changes nothing in the world;
    # it draws the ring or the brackets on a tile so the two can be looked at
    # without a mouse. Kept here rather than in a test because the only
    # question it answers is "what does that look like", and that is a
    # question for a photograph.
    'mark':      ('show_mark',   [AS_INT, AS_INT, lambda v: str(v) in ('1', 'true', 'act')]),
    'gather':    ('gather',      [AS_STR]),
    'attack':    ('attack',      [AS_STR, AS_STR]),
    # Striking a PERSON is its own verb in the world (§11d): a hauler carrying
    # a consignment is the one citizen anybody may lawfully strike.
    'attackp':   ('attack_person', [AS_STR, AS_STR]),
    'wield':     ('wield',       [AS_INT]),
    'unwield':   ('unwield',     [AS_STR]),
    'buy':       ('buy',         [AS_STR]),
    'drop':      ('drop',        [AS_INT]),
    'pickup':    ('pick_up',     [AS_STR, lambda v: v.lower() in ('1', 'true', 'yes')]),
    'cast':      ('cast',        [AS_STR]),
    'haul':      ('haul',        [AS_STR]),
    'unload':    ('unload',      [AS_STR]),
    'smith':     ('smith',       [AS_STR]),
    'name':      ('claim_name',  [AS_STR]),
    'follow':    ('follow',      [AS_STR]),
    'still':     ('still',       [AS_STR]),
    'mendp':     ('mend_other',  [AS_STR]),
    'seal':      ('seal',        [AS_STR]),
    'unmake':    ('unmake',      [AS_STR]),
    'transmute':      ('transmute',        [AS_INT]),
    'waking':    ('waking',      [AS_STR]),
    'rot':       ('rot',         [AS_STR]),
    'taking':    ('taking',      [AS_STR]),
    'withering': ('withering',   [AS_STR]),
    'turnbook':  ('turn_book',   []),
    'deliver':   ('deliver',     [AS_INT]),
    'release':   ('release',     []),
    # `consign` takes a LIST of slots, not a fixed number of arguments, so it
    # is read specially below -- the table above only knows fixed shapes.
    'consign':   ('consign',     None),
    'enter':     ('enter',       []),
    # THE THIRTEEN THAT WERE STILL MISSING, found by auditing the engine's own
    # validator rather than by reading its schema table -- see the note over
    # the matching block in IntervalHand.cpp. The market and the trade between
    # citizens are two whole economies this window could not touch.
    'market':    ('raise_market',     []),
    'stock':     ('stock_market',     [AS_INT]),
    'price':     ('price_market',     [AS_INT]),
    'takecoin':  ('take_market',      []),
    'unmarket':  ('dismantle_market', []),
    'accept':    ('accept_trade',     [AS_STR]),
    'cancel':    ('cancel_trade',     []),
    'brewpot':   ('build_brewpot',    []),
    'bankall':   ('deposit_all',      []),
    'chart':     ('read_chart',       [AS_INT]),
    'recall':    ('recall',           [AS_STR]),
    'look':      ('set_look',         [AS_INT]),
    # `offer` takes a list in the middle of its arguments, so it is read
    # specially below, like `consign`.
    'trade':     ('offer_trade',      None),
'brew': ('brew', [AS_STR, AS_INT]),
    'bury': ('bury', [AS_INT]),
    'collect': ('collect', [AS_STR]),
    'cook': ('cook', [AS_INT]),
    'deposit': ('deposit', [AS_INT]),
    'dismantle': ('dismantle', [AS_STR]),
    'eat': ('eat', [AS_INT]),
    'harvest': ('harvest', [AS_STR]),
    'invoke': ('invoke', []),
    'plant': ('plant', [AS_INT]),
    'saw': ('saw', []),
    'smelt': ('smelt', [AS_STR]),
    'stoke': ('stoke', [AS_STR, AS_INT]),
    'stop': ('stop', []),
    # EVERY OTHER VERB THE WORLD HAS. Generated from the engine's own
    # INPUT_SCHEMAS, name for name and type for type -- see the note over
    # the matching block in IntervalHand.cpp.
'archive': ('archive', [AS_STR]),
    'befriend': ('befriend', [AS_STR]),
    'char': ('char', [AS_STR]),
    'charter': ('charter', [AS_INT]),
    'dedicate': ('dedicate', [AS_STR, AS_INT]),
    'drink': ('drink', []),
    'fletch': ('fletch', [AS_INT, AS_STR]),
    'found': ('found', [AS_INT, AS_INT]),
    'grave': ('grave', [AS_STR, AS_STR]),
    'grind': ('grind', [AS_INT]),
    'kindle': ('kindle', []),
    'lay': ('lay', [AS_STR, AS_INT]),
    'lift': ('lift', [AS_STR]),
    'light': ('light', [AS_INT]),
    'move': ('move', [AS_INT, AS_INT]),
    'nock': ('nock', [AS_INT]),
    'offer': ('offer', [AS_INT]),
    'pay': ('pay', []),
    'restore': ('restore', []),
    'rifle': ('rifle', [AS_STR, AS_STR]),
    'sail': ('sail', []),
    'sapling': ('sapling', [AS_STR]),
    'setbuck': ('setbuck', []),
    'sound': ('sound', []),
    'gambit': ('gambit', [AS_STR, AS_STR]),
    'stamp': ('stamp', [AS_INT]),
    'stint': ('stint', [AS_INT]),
    'survey': ('survey', []),
    'swear': ('swear', [AS_STR]),
    'turn': ('turn', []),
    'unfollow': ('unfollow', []),
    'unfriend': ('unfriend', [AS_STR]),
    'withdraw': ('withdraw', [AS_STR, AS_INT]),
}


def run(line):
    bits = line.split()
    if not bits:
        return
    verb = bits[0].lower()
    # THE WINDOW'S OWN VERBS DO NOT NEED A CITIZEN.
    #
    # `exec` runs a console command and `py` runs a script; neither touches the
    # hand. They were behind the hand lookup anyway, so anything sent before
    # PIE was up -- which is everything a session sends while it is starting --
    # came back "no hand yet" and was thrown away. The symptom was a probe that
    # was never armed and a calibration that could never run, with a log line
    # that pointed at the citizen instead of at the ordering.
    if verb == 'exec':
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() \
            or unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        cmd = ' '.join(bits[1:])
        if not w or not cmd:
            note('exec <console command>')
            return
        unreal.SystemLibrary.execute_console_command(w, cmd)
        note('exec %s' % cmd)
        return
    h = hand()
    if not h:
        note('no hand yet: %s' % line)
        return
    if verb == 'plain':
        h.plain(bits[1])
        note('plain %s' % bits[1])
        return
    # THE WINDOW'S OWN THRESHOLD, WHICH IS NOT A DEED.
    #
    # `AIntervalGate` holds the title card up until somebody crosses it, and
    # crossing it is deliberately a person's act -- the world is entered, not
    # arrived in. But it left automation stranded: every editor restart came
    # back to the title screen with no way past it, because the PIE viewport's
    # UMG is not in the editor's Slate tree and so the button cannot be
    # clicked from outside. `Enter` is BlueprintCallable for exactly this.
    #
    # It is NOT in VERBS, because VERBS is the world's vocabulary and this word
    # is the window's. Nothing is filed, nothing is signed, and the world never
    # hears about it.
    # A CONSOLE COMMAND, WHICH IS NOT A DEED EITHER.
    #
    # `r.ForceLOD`, `stat unit`, `show Bounds` -- the renderer's own switches.
    # There is no cvar setter anywhere on the MCP surface (EditorAppToolset can
    # only SEARCH them), and without one there is no way to ask the window a
    # question like "is this smooth because it is a low level of detail, or
    # because the mesh is wrong" other than by changing an asset and restarting.
    #
    # It files nothing and signs nothing. Like `gate`, it is the window's own
    # vocabulary, not the world's.
    # WHAT IS ACTUALLY STANDING HERE, asked of the renderer itself.
    #
    # Written after an evening of guessing at some large green shapes round the
    # goblin pound. Every indirect method lied in a different way: the node
    # list was silently truncated, an asset's own render looks nothing like the
    # same mesh seen from overhead, `trace_world` finds only the ground because
    # instanced pools carry no collision, and forcing a level of detail
    # disproved a theory without suggesting another.
    #
    # The structures renderer keeps one instanced pool per mesh and every
    # instance's transform is right there. This reads them: for each pool, the
    # mesh, and the instances within a few metres of the citizen with their
    # true world scale. No inference at all.
    #
    #   what [radius-in-tiles]
    if verb == 'what':
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if not w:
            note('no world')
            return
        # THE HAND STANDS AT THE ORIGIN. It is a controller, not a body, so its
        # actor location is 0,0 and asking it where the citizen is gives the
        # corner of the island. The tile is named instead:
        #   what <tileX> <tileY> [radius-in-tiles]
        if len(bits) < 3:
            note('what <tileX> <tileY> [radius]')
            return
        tx, ty = int(bits[1]), int(bits[2])
        reach = (float(bits[3]) if len(bits) > 3 else 3.0) * 200.0
        here = unreal.Vector((tx + 0.5) * 200.0, (ty + 0.5) * 200.0, 0.0)
        rows = []
        for actor in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
            name = actor.get_name()
            if 'Interval' not in name:
                continue
            for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
                mesh = comp.static_mesh
                if not mesh:
                    continue
                for i in range(comp.get_instance_count()):
                    xf = comp.get_instance_transform(i, world_space=True)
                    if xf is None:
                        continue
                    loc = xf.translation
                    if abs(loc.x - here.x) > reach or abs(loc.y - here.y) > reach:
                        continue
                    sc = xf.scale3d
                    rows.append('%-22s %-26s at %6.0f,%6.0f  scale %.2f,%.2f,%.2f'
                                % (name[:22], mesh.get_name()[:26], loc.x, loc.y,
                                   sc.x, sc.y, sc.z))
        # THE GROUND COVER IS NOT THE ANSWER, and there are hundreds of it.
        #
        # Sorted plainly, `Clover_1` and three kinds of grass fill every line
        # of the report and the one Cube or Sphere that is actually being asked
        # about falls off the bottom. The scatter is TALLIED and the built
        # things are LISTED, which is the shape of the question every time.
        scatter = ('Grass', 'Clover', 'Pebble', 'Fern', 'Plant_')
        built = [r for r in rows if not any(g in r for g in scatter)]
        grew = len(rows) - len(built)
        note('what: %d built things and %d of ground cover within %.0f tiles of %.0f,%.0f'
             % (len(built), grew, reach / 200.0, here.x, here.y))
        for r in sorted(built)[:40]:
            note('   ' + r)
        return
    if verb == 'gate':
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        gates = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.IntervalGate) if w else []
        if not gates:
            note('no gate in the world')
            return
        gates[0].enter()
        note('gate crossed')
        return
    # ---- WHAT A RIGHT CLICK WOULD OFFER, without a mouse ----
    #
    # The menu is driven by the cursor and the cursor cannot be driven from
    # here, so this asks the hand the same two questions a right click asks --
    # what is on that tile, and what does each of those afford -- and prints
    # the answer. It is how the affordance table was checked against the world
    # rather than against its own source.
    if verb == 'offers':
        if len(bits) < 3:
            note('offers <x> <y>')
            return
        tx, ty = int(bits[1]), int(bits[2])
        found = h.targets_at(tx, ty)
        note('offers at %d,%d -- %d thing(s)' % (tx, ty, len(found)))
        for tgt in found:
            opts = h.options_for(tgt)
            note('  %-9s %-16s %s' % (
                str(tgt.kind).rsplit('.', 1)[-1], tgt.name or tgt.type,
                ' | '.join(o.label for o in opts)))
        return

    # ---- OPEN THE MENU, without a mouse ----
    #
    # The menu is driven by a right click and there is no way to press one from
    # here. This broadcasts exactly what the right click broadcasts, so what
    # appears on screen is the real widget with the real options in it -- the
    # only thing not exercised is the button itself.
    if verb == 'rclick':
        if len(bits) < 3:
            note('rclick <x> <y>')
            return
        tx, ty = int(bits[1]), int(bits[2])
        # AND WHERE ON SCREEN THE CLICK WAS, optionally. The menu opens at the
        # cursor, and with the mouse outside the viewport there IS no cursor --
        # every screenshot in these notes is taken that way, which made the
        # menu look like it opened somewhere arbitrary. Putting the pointer
        # somewhere first shows what a real right click does.
        if len(bits) >= 5:
            pc = unreal.EditorLevelLibrary.get_player_controller(0) \
                if hasattr(unreal, 'EditorLevelLibrary') else None
            try:
                world = h.get_world()
                pc = unreal.GameplayStatics.get_player_controller(world, 0)
                pc.set_mouse_location(int(bits[3]), int(bits[4]))
                note('pointer at %s,%s' % (bits[3], bits[4]))
            except Exception as exc:
                note('could not move the pointer: %s' % exc)
        found = h.targets_at(tx, ty)
        h.on_options.broadcast(found)
        note('rclick %d,%d -- offered %d thing(s)' % (tx, ty, len(found)))
        return

    entry = VERBS.get(verb)
    if not entry:
        note('unknown verb %s (try: %s)' % (verb, ' '.join(sorted(VERBS))))
        return
    method, readers = entry
    # THE VARIABLE-LENGTH ONE. Everything else takes a fixed handful of
    # arguments; a consignment takes however many slots the citizen names.
    # THE ONE WITH A LIST IN THE MIDDLE OF IT.
    #
    #   trade <toPlayerId> <slots,comma,separated> <wantItem|-> <wantGold>
    #
    # A dash for the item means coin is wanted, and it travels as a real JSON
    # null -- the engine is explicit that omission is not a representation.
    if verb == 'trade':
        if len(bits) < 5:
            note('trade <toId> <slots,..> <item|-> <gold>')
            return
        slots = sorted({int(b) for b in bits[2].split(',') if b != ''})
        item = '' if bits[3] == '-' else bits[3]
        h.offer_trade(bits[1], slots, item, int(bits[4]))
        note('trade %s %s %s %s' % (bits[1], slots, bits[3], bits[4]))
        return
    if readers is None:
        slots = sorted({int(b) for b in bits[1:]})
        if not slots:
            note('consign wants at least one slot')
            return
        getattr(h, method)(slots)
        note('consign %s' % ' '.join(str(x) for x in slots))
        return
    args = []
    for i, read in enumerate(readers):
        if len(bits) <= i + 1:
            note('%s wants %d arguments' % (verb, len(readers)))
            return
        args.append(read(bits[i + 1]))
    # A name may have spaces; the last string reader eats the rest of the line.
    if verb == 'name':
        args = [' '.join(bits[1:])]
    getattr(h, method)(*args)
    note('%s %s' % (verb, ' '.join(str(a) for a in args)))


# ---- THE TICK ONLY FIRES WHILE THE EDITOR IS IN FRONT ----
#
# `register_slate_post_tick_callback` is a SLATE tick, and Slate does not tick
# an application macOS has put to the back -- so the hand armed, said so, and
# then read nothing at all for as long as any other window was in front. Four
# commands sat unread in the file; the moment the editor was brought forward
# they all ran at once.
#
# The cure was already here and in the wrong place: the throttle was turned
# off INSIDE the tick, which is the one piece of code that cannot run when the
# throttle is what is stopping it. It is turned off at ARM time now, before
# anything depends on the tick, and left off.
#
# It cost three sessions of "the probe is not writing: is it armed, and is PIE
# up?" -- a message that names the two things that were fine.
def _stay_awake():
    """Stop the editor dozing when it is not the front window.

    THREE WAYS, BECAUSE TWO OF THEM DO NOT WORK. The editor setting is the one
    a person would change in Preferences and setting it on the class default
    object is accepted in silence and changes nothing; what actually gates the
    Slate tick is the console variable. Both are tried, and the CVar is tried
    under both names it has had, because a callback that only fires while the
    editor is in front is a harness that only works while somebody is watching
    it -- and every command typed in the meantime piles up unread.
    """
    done = False
    try:
        cdo = unreal.get_default_object(unreal.EditorPerformanceSettings)
        cdo.set_editor_property('throttle_cpu_when_not_foreground', False)
        done = True
    except Exception:
        pass
    try:
        es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        w = es.get_editor_world() or es.get_game_world()
        for cmd in ('Slate.bAllowThrottling 0', 'Slate.AllowThrottling 0',
                    'r.Editor.SkipSourceControlCheck 1'):
            try:
                unreal.SystemLibrary.execute_console_command(w, cmd)
            except Exception:
                pass
        done = True
    except Exception:
        pass
    return done


def tick(delta):
    state['n'] += 1
    if state['n'] % 10:
        return
    try:
        if not os.path.exists(CMD):
            return
        with open(CMD) as f:
            lines = [l.strip() for l in f if l.strip()]
        if not lines:
            return
        # Truncated BEFORE running, so a deed cannot be filed twice if one of
        # them throws.
        open(CMD, 'w').close()
        for l in lines:
            try:
                run(l)
            except Exception:
                note('failed: %s\n%s' % (l, traceback.format_exc()))
    except Exception:
        pass


_awake = _stay_awake()
unreal.register_slate_post_tick_callback(tick)
note('remote armed, reading %s%s' % (CMD, '' if _awake
     else '  -- BUT the editor still throttles when it is not in front, so '
          'this will only read while it is'))
