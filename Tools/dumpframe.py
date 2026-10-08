# A hierarchical breakdown of one frame, written to the log.
#
# `stat dumpframe` is the one profiling command that reports into the LOG
# rather than onto the screen, which makes it the only one reachable from
# here. It has to be fired once the world is actually up, and `-ExecCmds` runs
# at startup when there is nothing to profile -- so this waits, from inside a
# tick callback, and then fires it.
import unreal

WAIT = 60            # frames to let the world build before looking at one
state = {'n': 0, 'done': False, 'handle': None}


def world():
    try:
        return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    except Exception:
        return None


def tick(delta):
    if state['done']:
        return
    state['n'] += 1
    if state['n'] < WAIT:
        return
    state['done'] = True
    w = world()
    unreal.log('DUMPFRAME firing at frame %d, world %s' % (state['n'], w))
    for cmd in ('stat dumpframe -ms=8',):
        try:
            unreal.SystemLibrary.execute_console_command(w, cmd)
        except Exception as e:
            unreal.log('DUMPFRAME failed: %s' % e)


state['handle'] = unreal.register_slate_post_tick_callback(tick)
unreal.log('DUMPFRAME armed')
