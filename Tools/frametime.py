# How long a frame actually takes, sampled from inside the editor.
#
# WHY THIS EXISTS. `stat unit` is the obvious answer and is out of reach here:
# there is no console-command tool on the MCP surface, and `-ExecCmds` runs
# before any viewport exists, so a `stat` at startup attaches to nothing. What
# IS reachable is the console command `py`, which runs a file -- and Python
# inside the editor can register a tick callback and time the frames itself.
#
# It samples continuously and writes a rolling report, so it can be started
# before the world is built and read at any point afterwards:
#
#   UE_EXEC='py .../frametime.py' ue.sh     # start it
#   ...simulate...
#   cat <scratchpad>/frametime.json         # read it
#
# It measures the EDITOR drawing the world, which is not the same as a packaged
# build and is slower. It is a budget to work against, not a shipping number.
import json, time
import unreal

REPORT = ('/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/'
          'd4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/frametime.json')

WINDOW = 240          # frames per report -- a few seconds at any plausible rate
state = {'last': None, 'gaps': [], 'reports': 0}


def wake():
    """Keep the editor from dozing, every tick, because once is not enough.

    Unreal throttles the editor to about three frames a second whenever its
    window is not in the foreground. Setting it false right after launch is
    not reliable -- the editor re-reads the setting as it finishes starting
    up, and a measurement taken after that comes back at 343 ms and looks
    like a catastrophically slow window rather than a sleeping editor. Setting
    it every tick costs nothing and cannot lose the race.
    """
    try:
        cdo = unreal.get_default_object(unreal.EditorPerformanceSettings)
        if cdo.get_editor_property('throttle_cpu_when_not_foreground'):
            cdo.set_editor_property('throttle_cpu_when_not_foreground', False)
    except Exception:
        pass


def tick(delta):
    wake()
    now = time.perf_counter()
    if state['last'] is not None:
        state['gaps'].append((now - state['last']) * 1000.0)
    state['last'] = now
    if len(state['gaps']) < WINDOW:
        return
    g = sorted(state['gaps'])
    state['gaps'] = []
    state['reports'] += 1
    n = len(g)
    out = {
        'frames': n,
        'report': state['reports'],
        # THE MEDIAN AND THE NINETY-NINTH, not the mean. A mean hides the
        # hitches, and a hitch is what a person actually notices -- one frame
        # in a hundred taking a third of a second is a stutter you can see and
        # a mean you cannot.
        'ms_median': round(g[n // 2], 2),
        'ms_p90': round(g[int(n * 0.90)], 2),
        'ms_p99': round(g[min(n - 1, int(n * 0.99))], 2),
        'ms_worst': round(g[-1], 2),
        'fps_median': round(1000.0 / max(0.01, g[n // 2]), 1),
    }
    try:
        json.dump(out, open(REPORT, 'w'), indent=1)
    except Exception:
        pass


handle = unreal.register_slate_post_tick_callback(tick)
unreal.log('FRAMETIME sampling started, writing %s' % REPORT)
