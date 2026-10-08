#!/usr/bin/env python3
"""Build the window's Niagara systems.

NS_Hearth is what a fire looks like from above: a thin column of smoke and a
few sparks. It is attached to every hearth the structures actor already lights,
so nothing here decides where a fire is -- the world does, and TendFires
already sorted them by distance and budgeted them.

EVERY NUMBER IN HERE IS A LOOK, not a fact about the world. How fast smoke
climbs and how grey it is are this window's opinion; that a forge is burning
is not.
"""
import json
import rpc as _rpc

T = 'NiagaraToolsets.NiagaraToolset_System'
AST = 'editor_toolset.toolsets.asset.AssetTools'
FOLDER = '/Game/Interval/FX'
TEMPLATE = '/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight'
FOUNTAIN = '/Niagara/DefaultAssets/Templates/Emitters/Fountain.Fountain'


def call(tool, args):
    return _rpc.call(T, tool, args)


def say(label, out):
    if 'returnValue' not in out:
        print('  !! %-28s %s' % (label, out[:220]))
    return out


class Sys:
    """One system, and the reference-building that every call to it needs."""

    def __init__(self, name):
        self.name = name
        self.path = '%s/%s.%s' % (FOLDER, name, name)
        _rpc.call(AST, 'delete', {'path': '%s/%s' % (FOLDER, name)})
        say('create ' + name, call('CreateNiagaraSystem', {
            'assetName': name, 'assetPath': FOLDER,
            'templateSystem': {'refPath': TEMPLATE}}))

    def ref(self, **kw):
        # Every reference wants all six fields present, even the empty ones.
        d = {'system': {'refPath': self.path}, 'emitterName': '', 'scriptName': '',
             'moduleName': '', 'rendererIndex': -1, 'inputNameStack': []}
        d.update(kw)
        return d

    def emitter(self, name):
        say('emitter ' + name, call('AddEmitter', {
            'system': {'refPath': self.path},
            'templateEmitter': {'refPath': FOUNTAIN}, 'emitterName': name}))
        return name

    def drop(self, emitter, script, module):
        say('remove ' + module, call('RemoveModule', {
            'moduleToRemove': self.ref(emitterName=emitter, scriptName=script,
                                       moduleName=module)}))

    def add(self, emitter, script, asset):
        say('module ' + asset.rsplit('/', 1)[-1], call('AddModule', {
            'moduleLocationRef': self.ref(emitterName=emitter, scriptName=script),
            'moduleAsset': {'refPath': asset}}))

    def put(self, emitter, script, module, names, struct, value):
        if not isinstance(names, list):
            names = [names]
        say('%s.%s' % (module, names[-1]), call('SetStackInputData', {
            'stackInputRef': self.ref(emitterName=emitter, scriptName=script,
                                      moduleName=module, inputNameStack=names),
            'inputData': {'struct': {'refPath': struct}, 'value': value}}))

    def link(self, emitter, script, module, names, variable, struct):
        """Point a module input at a named variable instead of a literal."""
        if not isinstance(names, list):
            names = [names]
        say('%s.%s' % (module, names[-1]), call('SetStackInputData', {
            'stackInputRef': self.ref(emitterName=emitter, scriptName=script,
                                      moduleName=module, inputNameStack=names),
            'inputData': {
                'struct': {'refPath': '/Script/NiagaraEditor.NiagaraExt_StackInputData_Linked'},
                'value': {'linkedVariable': {
                    'name': variable,
                    'type': {'classStructOrEnum': {'refPath': struct}}}}}}))

    def user(self, name, struct, default, note):
        say('user ' + name, call('AddUserVariables', {
            'system': {'refPath': self.path},
            'variablesToAdd': [{'name': name, 'description': note,
                                'type': {'classStructOrEnum': {'refPath': struct}},
                                'defaultValue': {'struct': {'refPath': struct},
                                                 'value': default}}]}))

    def renderer(self, emitter, values):
        say('renderer ' + emitter, call('SetRendererData', {
            'renderer': self.ref(emitterName=emitter, rendererIndex=0),
            'rendererData': {'propertyValues': json.dumps(values)}}))

    def settle(self, rounds=6):
        """Apply every fix Niagara offers, until it stops offering any.

        A force module added to the bottom of the particle update stack lands
        AFTER SolveForcesAndVelocity, which is where the accumulated force is
        turned into motion -- so the force is written a frame too late and the
        emitter reports an error rather than quietly doing nothing. Niagara
        knows exactly how to fix that and says so; taking it up is more honest
        than counting module indices here and hoping the template never gains
        one.
        """
        def ask():
            # A COMPILE IN FLIGHT ANSWERS WITH PROSE, NOT JSON. Niagara
            # refuses to collect stack issues while it is compiling and says so
            # in plain English, which json.loads treats as a crash -- and that
            # took out a whole rebuild partway through, after the materials had
            # been replaced and before the look asset was rewritten.
            raw = call('GetStackIssues', {'system': {'refPath': self.path}})
            try:
                return json.loads(raw)['returnValue']
            except Exception:
                return None

        for _ in range(rounds):
            out = ask()
            if out is None:
                continue
            todo = [(i['issueId'], f['fixId'], f.get('description', ''))
                    for i in out['issues'] if i['severity'] == 'Error'
                    for f in i.get('fixes', []) if f.get('fixId')]
            if not todo:
                break
            for issue, fix, what in todo:
                r = call('ApplyStackIssueFix', {'system': {'refPath': self.path},
                                                'issueId': issue, 'fixId': fix})
                print('   fix:', what, '->', 'ok' if 'returnValue' in r else r[:120])
        out = ask()
        if out is None:
            print('issues: could not be read (a compile was in flight)')
            return
        print('issues: %d errors, %d warnings' % (out['numErrors'], out['numWarnings']))
        for i in out['issues']:
            if i['severity'] != 'Info':
                print('   %s: %s' % (i['severity'], i['shortDescription']))

    def save(self):
        print('save:', _rpc.call(AST, 'save_assets',
                                 {'asset_paths': ['%s/%s' % (FOLDER, self.name)]})[:60])


# STOP THE SESSION FIRST. This script deletes the system and builds another at
# the same path; doing that while a world is simulating with fourteen
# components pointing at it leaves the delete refused and the create silently
# skipped, and the only symptom is a save reporting that the asset it was just
# asked to write does not exist.
_rpc.call('EditorToolset.EditorAppToolset', 'StopPIE', {})

F = '/Script/Niagara.NiagaraFloat'
V3 = '/Script/CoreUObject.Vector3f'
COL = '/Script/CoreUObject.LinearColor'
BOOL = '/Script/Niagara.NiagaraBool'
INT = '/Script/Niagara.NiagaraInt32'
DI = '/Script/NiagaraEditor.NiagaraExt_StackInputData_DataInterface'


def curve(points, cubic=True):
    """A Niagara curve data interface, written as the key list it stores.

    Curves are the whole reason these systems can look like anything. A puff
    that grows and an alpha that rises, holds and dies are both curves, and
    both of them are what stops a particle system reading as a particle
    system -- linear anything is the tell.
    """
    mode = 'RCIM_Cubic' if cubic else 'RCIM_Linear'
    keys = [{'interpMode': mode, 'tangentMode': 'RCTM_Auto',
             'tangentWeightMode': 'RCTWM_WeightedNone',
             'time': t, 'value': v, 'arriveTangent': 0.0, 'arriveTangentWeight': 0.0,
             'leaveTangent': 0.0, 'leaveTangentWeight': 0.0} for t, v in points]
    return {'propertyValues': json.dumps({
        'Curve': {'keys': keys, 'defaultValue': 3.4028234663852886e+38,
                  'preInfinityExtrap': 'RCCE_Constant',
                  'postInfinityExtrap': 'RCCE_Constant'},
        'CurveAsset': 'None', 'bUseLUT': True, 'bExposeCurve': False,
        'bOptimizeLUT': True, 'bOverrideOptimizeThreshold': False,
        'OptimizeThreshold': 0.01, 'ExposedName': 'Float Curve'})}


SPAWN = 'ParticleSpawnScript'
UPDATE = 'ParticleUpdateScript'
EMIT = 'EmitterUpdateScript'
MOD = '/Niagara/Modules/'


# ---------------------------------------------------------------------------
# NS_Hearth
#
# A fire seen from four hundred metres up is not flames. It is a smudge of
# smoke leaning downwind and, at night, a few sparks. Both of those read at
# this camera's distance and the flames themselves do not, which is why the
# smoke gets the budget.
h = Sys('NS_Hearth')
# THE WIND, PUSHED IN FROM OUTSIDE. Niagara cannot read a material parameter
# collection, so the structures actor reads `Gale` off the same collection the
# grass reads and writes it here as a world-space acceleration. One number,
# one source, and the smoke leans the way the meadow leans.
h.user('Wind', V3, {'x': 0.0, 'y': 0.0, 'z': 0.0},
       'World-space wind acceleration, written each frame by AIntervalStructures.')

# ---- smoke ----
h.emitter('Smoke')
# TWENTY-SIX A SECOND, EACH ONE FAINT.
#
# The first pass ran at a twelfth of this with each puff four times as solid,
# and from directly above -- the only angle this window ever uses -- the column
# came out as a STACK OF COINS: discrete blobs with daylight between them,
# which is the exact failure smoke.hlsl was written to avoid and which no
# amount of edge noise can hide. What hides it is overlap. Many thin puffs
# accumulate into a column with no countable parts; few solid ones cannot. The fountain template is a fountain: ninety
# particles a second, each living under two seconds. Smoke is the other shape
# entirely -- very few, very large, very long-lived -- and a column made of
# ninety small puffs a second is a solid grey tube.
h.put('Smoke', EMIT, 'SpawnRate', 'SpawnRate', F, {'value': 26.0})

h.put('Smoke', SPAWN, 'InitializeParticle', 'Lifetime Min', F, {'value': 3.4})
h.put('Smoke', SPAWN, 'InitializeParticle', 'Lifetime Max', F, {'value': 6.8})
# Warm grey, and thin. The alpha here is the puff's TOTAL opacity: smoke you
# cannot see through is steam off a kettle, and a roof you cannot see through
# the smoke of looks like a hole in the village.
h.put('Smoke', SPAWN, 'InitializeParticle', 'Color', COL,
      {'r': 0.44, 'g': 0.43, 'b': 0.415, 'a': 0.26})
h.put('Smoke', SPAWN, 'InitializeParticle', 'Uniform Sprite Size Min', F, {'value': 46.0})
h.put('Smoke', SPAWN, 'InitializeParticle', 'Uniform Sprite Size Max', F, {'value': 108.0})
h.put('Smoke', SPAWN, 'InitializeParticle', 'Mass Min', F, {'value': 0.6})
h.put('Smoke', SPAWN, 'InitializeParticle', 'Mass Max', F, {'value': 1.1})
h.put('Smoke', SPAWN, 'ShapeLocation', 'Sphere Radius', F, {'value': 9.0})
# Leaving the chimney, not being fired out of it.
h.put('Smoke', SPAWN, 'AddVelocity', 'Velocity Speed', F, {'value': 105.0})
h.put('Smoke', SPAWN, 'AddVelocity', 'Cone Angle', F, {'value': 22.0})
# BUOYANCY, WHICH IS GRAVITY UPWARDS. The template pulls particles down at a
# full g because it is throwing water. Hot air goes the other way, weakly, and
# the drag below is what gives the column its shape: it accelerates for a
# metre or two and then simply drifts.
h.put('Smoke', UPDATE, 'GravityForce', 'Gravity', V3, {'x': 0.0, 'y': 0.0, 'z': 42.0})
h.put('Smoke', UPDATE, 'Drag', 'Drag', F, {'value': 0.80})
h.put('Smoke', UPDATE, 'ScaleColor', ['Scale Alpha', 'FloatCurve'], DI,
      curve([(0.0, 0.0), (0.14, 1.0), (0.55, 0.88), (1.0, 0.0)]))

# A puff EXPANDS as it rises. Without this the column is a line of identical
# stamps, which is the loudest tell a smoke effect has.
h.add('Smoke', UPDATE, MOD + 'Update/Size/ScaleSpriteSize.ScaleSpriteSize')
h.put('Smoke', UPDATE, 'ScaleSpriteSize', 'Uniform Curve Sprite Scale', DI,
      curve([(0.0, 0.45), (0.25, 1.30), (1.0, 3.70)]))

# AND IT WANDERS. Curl noise is divergence-free, so it swirls the column
# without blowing it apart -- which is precisely the difference between smoke
# and a spray.
h.add('Smoke', UPDATE, MOD + 'Update/Forces/CurlNoiseForce.CurlNoiseForce')
h.put('Smoke', UPDATE, 'CurlNoiseForce', 'Noise Strength', F, {'value': 95.0})
h.put('Smoke', UPDATE, 'CurlNoiseForce', 'Noise Frequency', F, {'value': 0.008})

# WHERE THE WIND COMES FROM. Not from here: the hour already works out how hard
# it is blowing from the world's own overcast and rain, and the structures
# actor pushes that in as `User.Wind` each frame. The same gale that leans the
# grass leans the smoke, because it is literally the same number.
h.add('Smoke', UPDATE, MOD + 'Update/Forces/AccelerationForce.AccelerationForce')
h.link('Smoke', UPDATE, 'AccelerationForce', 'Acceleration', 'User.Wind', V3)

# ---- embers ----
h.emitter('Embers')
h.put('Embers', EMIT, 'SpawnRate', 'SpawnRate', F, {'value': 9.0})
h.put('Embers', SPAWN, 'InitializeParticle', 'Lifetime Min', F, {'value': 0.9})
h.put('Embers', SPAWN, 'InitializeParticle', 'Lifetime Max', F, {'value': 2.2})
h.put('Embers', SPAWN, 'InitializeParticle', 'Color', COL,
      {'r': 1.0, 'g': 0.46, 'b': 0.13, 'a': 1.0})
h.put('Embers', SPAWN, 'InitializeParticle', 'Uniform Sprite Size Min', F, {'value': 3.5})
h.put('Embers', SPAWN, 'InitializeParticle', 'Uniform Sprite Size Max', F, {'value': 8.5})
h.put('Embers', SPAWN, 'ShapeLocation', 'Sphere Radius', F, {'value': 7.0})
h.put('Embers', SPAWN, 'AddVelocity', 'Velocity Speed', F, {'value': 140.0})
h.put('Embers', SPAWN, 'AddVelocity', 'Cone Angle', F, {'value': 36.0})
# A spark is heavy enough to arc. It goes up on the thermal and comes down,
# and the ones that come down are what makes it a fire rather than a fountain.
h.put('Embers', UPDATE, 'GravityForce', 'Gravity', V3, {'x': 0.0, 'y': 0.0, 'z': -34.0})
h.put('Embers', UPDATE, 'Drag', 'Drag', F, {'value': 0.55})
# Flat: the ember material does its own dying, off the particle's age, because
# a spark goes out suddenly and a curve here would ramp it.
h.put('Embers', UPDATE, 'ScaleColor', ['Scale Alpha', 'FloatCurve'], DI,
      curve([(0.0, 1.0), (1.0, 1.0)]))
h.add('Embers', UPDATE, MOD + 'Update/Forces/CurlNoiseForce.CurlNoiseForce')
h.put('Embers', UPDATE, 'CurlNoiseForce', 'Noise Strength', F, {'value': 110.0})
h.put('Embers', UPDATE, 'CurlNoiseForce', 'Noise Frequency', F, {'value': 0.02})
h.add('Embers', UPDATE, MOD + 'Update/Forces/AccelerationForce.AccelerationForce')
h.link('Embers', UPDATE, 'AccelerationForce', 'Acceleration', 'User.Wind', V3)


# ---- what the sprites are made of ----
#
# The template's default sprite material is an unlit disc, which is the thing
# smoke.hlsl exists to replace. bCastShadows off on both: a hearth's smoke
# casting a shadow costs a shadow map's worth of work to darken a roof nobody
# is looking at, and the embers are light sources and have no business
# blocking any.
h.renderer('Smoke', {
    'Material': {'refPath': '/Game/Interval/Materials/M_IntervalSmoke.M_IntervalSmoke'},
    'bCastShadows': False,
    # Translucent puffs overlapping each other have to be drawn far-to-near or
    # the column reads as flat cards. This is the cheap sort and it is enough.
    'SortMode': 'ViewDepth',
    'Alignment': 'Unaligned',
    'FacingMode': 'FaceCamera',
})
h.renderer('Embers', {
    'Material': {'refPath': '/Game/Interval/Materials/M_IntervalEmber.M_IntervalEmber'},
    'bCastShadows': False,
    'SortMode': 'None',           # additive: order does not matter
    'Alignment': 'Unaligned',
    'FacingMode': 'FaceCamera',
})

h.settle()
h.save()


# ---------------------------------------------------------------------------
# NS_Step
#
# The dust a pair of boots lifts. It is the smallest effect in here and close
# to the most valuable: a figure crossing a dry yard with nothing happening
# under it is SLIDING, and no amount of animation fixes that, because the tell
# is not the legs -- it is that the world does not notice them.
#
# SPAWNED PER UNIT OF TRAVEL, not per second. This is the whole trick. A rate
# in particles-per-second has to be turned on and off by somebody who knows
# whether the citizen is walking; spacing in centimetres simply emits nothing
# when nothing moves, and emits more when somebody runs, with nothing in C++
# asking any questions.
d = Sys('NS_Step')
d.user('Wind', V3, {'x': 0.0, 'y': 0.0, 'z': 0.0},
       'World-space wind acceleration, written each frame by AIntervalCitizens.')
# HOW DRY IT IS. Dust off wet ground is mud, and mud does not puff. The
# citizens actor reads `Wet` off the same collection the ground reads and
# writes one minus it here, so the dust simply stops during a shower and comes
# back as the road dries -- on the same lag the ground's own darkening uses.
d.user('Dry', F, {'value': 1.0},
       'One minus the ground wetness, written each frame by AIntervalCitizens.')

d.emitter('Dust')
d.drop('Dust', EMIT, 'SpawnRate')
d.add('Dust', EMIT, MOD + 'Emitter/SpawnPerUnit.SpawnPerUnit')
# A puff every twenty-six centimetres is about one a stride at a walk.
d.put('Dust', EMIT, 'SpawnPerUnit', 'Spawn Spacing', F, {'value': 26.0})
# AND NOT WHEN SOMEBODY IS RE-AIMED RATHER THAN WALKING. A pooled component
# that jumps eighty metres to a new owner has "travelled" eighty metres, and
# per-unit spawning would lay a line of dust the whole way. Anything past two
# metres in a frame is a teleport, not a step.
# The toggle carries a `Module.` prefix in the stack; the value it gates does
# not. That is not a typo, it is how a module-scope switch is addressed.
d.put('Dust', EMIT, 'SpawnPerUnit', 'Module.Use Max Movement Threshold', BOOL, {'value': -1})
d.put('Dust', EMIT, 'SpawnPerUnit', 'Max Movement Threshold', F, {'value': 200.0})
# FLIP THE GATE FIRST. An input whose edit condition is false is refused
# outright, which is a good deal more helpful than writing a value into a field
# the simulation will never read.
d.put('Dust', EMIT, 'SpawnPerUnit', 'Use Spawn Probability', BOOL, {'value': -1})
d.link('Dust', EMIT, 'SpawnPerUnit', 'Spawn Probability', 'User.Dry', F)

d.put('Dust', SPAWN, 'InitializeParticle', 'Lifetime Min', F, {'value': 0.55})
d.put('Dust', SPAWN, 'InitializeParticle', 'Lifetime Max', F, {'value': 1.30})
# Dry earth, and faint. Dust you can see clearly is a smoke grenade.
d.put('Dust', SPAWN, 'InitializeParticle', 'Color', COL,
      {'r': 0.50, 'g': 0.455, 'b': 0.38, 'a': 0.30})
d.put('Dust', SPAWN, 'InitializeParticle', 'Uniform Sprite Size Min', F, {'value': 10.0})
d.put('Dust', SPAWN, 'InitializeParticle', 'Uniform Sprite Size Max', F, {'value': 24.0})
d.put('Dust', SPAWN, 'InitializeParticle', 'Mass Min', F, {'value': 0.6})
d.put('Dust', SPAWN, 'InitializeParticle', 'Mass Max', F, {'value': 1.0})
d.put('Dust', SPAWN, 'ShapeLocation', 'Sphere Radius', F, {'value': 7.0})
# OUT AND ONLY JUST UP. A boot scuffs earth sideways; it does not launch it.
# A narrow upward cone here is what made the first pass look like a smoking
# ankle rather than a footfall.
d.put('Dust', SPAWN, 'AddVelocity', 'Velocity Speed', F, {'value': 26.0})
d.put('Dust', SPAWN, 'AddVelocity', 'Cone Angle', F, {'value': 70.0})
d.put('Dust', UPDATE, 'GravityForce', 'Gravity', V3, {'x': 0.0, 'y': 0.0, 'z': -18.0})
# Heavy drag: dust hangs and settles, it does not fly.
d.put('Dust', UPDATE, 'Drag', 'Drag', F, {'value': 2.40})
d.put('Dust', UPDATE, 'ScaleColor', ['Scale Alpha', 'FloatCurve'], DI,
      curve([(0.0, 0.0), (0.18, 1.0), (1.0, 0.0)]))
d.add('Dust', UPDATE, MOD + 'Update/Size/ScaleSpriteSize.ScaleSpriteSize')
d.put('Dust', UPDATE, 'ScaleSpriteSize', 'Uniform Curve Sprite Scale', DI,
      curve([(0.0, 0.60), (1.0, 2.40)]))
d.add('Dust', UPDATE, MOD + 'Update/Forces/AccelerationForce.AccelerationForce')
d.link('Dust', UPDATE, 'AccelerationForce', 'Acceleration', 'User.Wind', V3)

d.renderer('Dust', {
    'Material': {'refPath': '/Game/Interval/Materials/M_IntervalSmoke.M_IntervalSmoke'},
    'bCastShadows': False,
    'SortMode': 'ViewDepth',
    'Alignment': 'Unaligned',
    'FacingMode': 'FaceCamera',
})
d.settle()
d.save()
print('NOW RUN apply.py -- this replaced the assets and the look holds hard pointers')



# ---------------------------------------------------------------------------
# THE RITES: what a spell looks like when somebody casts it.
#
# Sorcery had no visual at all, and for a while it looked as though it could
# not have one: no spell sets an `action`, so nothing about a cast reached the
# window. It turned out the world records `deed` for every citizen on the
# interval they do something, the bridge was already forwarding it, and the
# window simply never read it. It does now, so these have something to fire
# them.
#
# FOUR SYSTEMS, NOT ELEVEN. Every spell takes its colour, its size and its
# height from the look asset, so one system serves several rites and they still
# read apart: a rot and an unmaking are both things flying outward, and what
# separates them is that one is dark and wet and slow and the other is bright
# and quick. Eleven near-identical systems would be eleven things to keep in
# step, and the first one anybody edited would drift.
#
# The four are the four SHAPES a spell in this world has:
#
#   burst    something comes apart, outward      unmake, rot
#   gather   something is drawn in               transmute, taking
#   ring     something spreads along the ground  still, seal, waking
#   rise     something climbs                    mend, mendp, anchor, invoke,
#                                                withering
#
# AND THEY ARE ONE-SHOTS. The dust and the hearth smoke run for as long as the
# thing they belong to exists; a cast is over in an interval. Each of these
# emits a single burst and then has nothing left to do, so the component that
# played it can be destroyed rather than pooled.
SMOKE = {'refPath': '/Game/Interval/Materials/M_IntervalSmoke.M_IntervalSmoke'}
# EMBER, NOT GLOW. `M_IntervalGlow` is not built for a sprite renderer and the
# stack says so, "materials might not render correctly"; `M_IntervalEmber` is
# the one the hearth's sparks already use, so it is known to work in exactly
# this place.
EMBER = {'refPath': '/Game/Interval/Materials/M_IntervalEmber.M_IntervalEmber'}


def rite(name, count, lifetime, speed, cone, gravity, drag, size,
         grow, material, rise=0.0, radial=None):
    """One shape of spell, neutral, with its colour left to the look asset."""
    r = Sys(name)
    # THE COLOUR IS NOT DECIDED HERE. A rot and an unmaking are the same
    # motion; what tells them apart is entirely this.
    r.user('Tint', COL, {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0},
           'The rite\'s colour, written by AIntervalCitizens from the look asset.')
    r.emitter('Motes')
    # ONE BURST. `SpawnRate` runs forever; this emits its handful and stops.
    r.drop('Motes', EMIT, 'SpawnRate')
    r.add('Motes', EMIT, MOD + 'Emitter/SpawnBurst_Instantaneous.SpawnBurst_Instantaneous')
    # A COUNT IS AN INTEGER, and the stack says so: it refuses a float here
    # with "expected NiagaraInt32", which is the kind of refusal worth having.
    r.put('Motes', EMIT, 'SpawnBurst_Instantaneous', 'Spawn Count', INT, {'value': int(count)})
    r.put('Motes', EMIT, 'SpawnBurst_Instantaneous', 'Spawn Time', F, {'value': 0.0})

    r.put('Motes', SPAWN, 'InitializeParticle', 'Lifetime Min', F, {'value': lifetime * 0.7})
    r.put('Motes', SPAWN, 'InitializeParticle', 'Lifetime Max', F, {'value': lifetime})
    r.link('Motes', SPAWN, 'InitializeParticle', 'Color', 'User.Tint', COL)
    r.put('Motes', SPAWN, 'InitializeParticle', 'Uniform Sprite Size Min', F,
          {'value': size * 0.6})
    r.put('Motes', SPAWN, 'InitializeParticle', 'Uniform Sprite Size Max', F,
          {'value': size})
    r.put('Motes', SPAWN, 'ShapeLocation', 'Sphere Radius', F,
          {'value': radial if radial is not None else 10.0})
    r.put('Motes', SPAWN, 'AddVelocity', 'Velocity Speed', F, {'value': speed})
    r.put('Motes', SPAWN, 'AddVelocity', 'Cone Angle', F, {'value': cone})
    if rise:
        r.add('Motes', SPAWN, MOD + 'Spawn/Location/AddVelocityInCone.AddVelocityInCone')
    r.put('Motes', UPDATE, 'GravityForce', 'Gravity', V3,
          {'x': 0.0, 'y': 0.0, 'z': gravity})
    r.put('Motes', UPDATE, 'Drag', 'Drag', F, {'value': drag})
    # In fast, out slow: a cast arrives and then lets go.
    r.put('Motes', UPDATE, 'ScaleColor', ['Scale Alpha', 'FloatCurve'], DI,
          curve([(0.0, 0.0), (0.10, 1.0), (0.55, 0.75), (1.0, 0.0)]))
    r.add('Motes', UPDATE, MOD + 'Update/Size/ScaleSpriteSize.ScaleSpriteSize')
    r.put('Motes', UPDATE, 'ScaleSpriteSize', 'Uniform Curve Sprite Scale', DI,
          curve(grow))
    r.renderer('Motes', {
        'Material': material,
        'bCastShadows': False,
        'SortMode': 'ViewDepth',
        'Alignment': 'Unaligned',
        'FacingMode': 'FaceCamera',
    })
    r.settle()
    r.save()
    return r


# SOMETHING COMES APART. Outward in every direction, fast, and it falls:
# an unmaking and a rot are both things that were whole a moment ago.
rite('NS_RiteBurst', 34, 0.85, 210.0, 180.0, -140.0, 1.6, 15.0,
     [(0.0, 1.30), (1.0, 0.35)], SMOKE, radial=12.0)
# SOMETHING IS DRAWN IN. Spawned out at arm's length and pulled back by a
# heavy drag with no speed of its own, so the motes close on the caster.
rite('NS_RiteGather', 26, 0.95, -150.0, 180.0, 0.0, 3.4, 12.0,
     [(0.0, 0.45), (0.7, 1.15), (1.0, 0.2)], EMBER, radial=95.0)
# SOMETHING SPREADS ALONG THE GROUND. Flat, wide and level: no gravity, no
# rise, a ring going out from the feet.
rite('NS_RiteRing', 40, 0.70, 330.0, 90.0, 0.0, 2.2, 18.0,
     [(0.0, 0.5), (0.35, 1.5), (1.0, 0.0)], SMOKE, radial=26.0)
# SOMETHING CLIMBS. A narrow column, slow, barely falling.
rite('NS_RiteRise', 22, 1.15, 120.0, 22.0, -10.0, 1.1, 13.0,
     [(0.0, 0.6), (0.5, 1.2), (1.0, 0.25)], EMBER, radial=16.0)

# ---- AND WHAT A SPELL LEAVES BEHIND ----
#
# A RITE ENDS AND A MARK DOES NOT. Everything above emits its handful and
# stops, because a casting is over inside the interval it happened in. These
# are the conditions that are left on whoever it landed on, and they last as
# long as the world says they last -- so they keep their SpawnRate, run for
# ever, and are switched on and off by the window instead.
#
# TWO SHAPES FOR SIX WORDS, on exactly the rites' argument. Burning, rotting
# and withering are all something happening TO a body and they read the same
# way: close in, rising, continuous. Rooted and stilled are both something
# holding a body in PLACE, which reads at the feet and not at the chest. What
# tells any two of them apart is the colour, which the look asset owns.
def mark(name, rate, lifetime, speed, cone, gravity, drag, size,
         grow, material, radial, alpha):
    """One condition, running for as long as somebody has it."""
    m = Sys(name)
    m.user('Tint', COL, {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0},
           "The mark's colour, written by AIntervalCitizens from the look asset.")
    m.emitter('Motes')
    # SpawnRate IS KEPT. This is the whole difference from a rite: the
    # emitter is meant to run until somebody turns it off.
    m.put('Motes', EMIT, 'SpawnRate', 'SpawnRate', F, {'value': float(rate)})

    m.put('Motes', SPAWN, 'InitializeParticle', 'Lifetime Min', F, {'value': lifetime * 0.7})
    m.put('Motes', SPAWN, 'InitializeParticle', 'Lifetime Max', F, {'value': lifetime})
    m.link('Motes', SPAWN, 'InitializeParticle', 'Color', 'User.Tint', COL)
    m.put('Motes', SPAWN, 'InitializeParticle', 'Uniform Sprite Size Min', F,
          {'value': size * 0.6})
    m.put('Motes', SPAWN, 'InitializeParticle', 'Uniform Sprite Size Max', F,
          {'value': size})
    m.put('Motes', SPAWN, 'ShapeLocation', 'Sphere Radius', F, {'value': radial})
    m.put('Motes', SPAWN, 'AddVelocity', 'Velocity Speed', F, {'value': speed})
    m.put('Motes', SPAWN, 'AddVelocity', 'Cone Angle', F, {'value': cone})
    m.put('Motes', UPDATE, 'GravityForce', 'Gravity', V3,
          {'x': 0.0, 'y': 0.0, 'z': gravity})
    m.put('Motes', UPDATE, 'Drag', 'Drag', F, {'value': drag})
    # IN SLOW AND OUT SLOW, unlike a rite. A mark that snapped to full
    # brightness would pulse once a particle lifetime and read as a flicker;
    # this one is meant to sit there and be noticed rather than announce
    # itself, because the citizen wearing it may be standing still for a
    # minute and nobody should have to watch a strobe for that long.
    m.put('Motes', UPDATE, 'ScaleColor', ['Scale Alpha', 'FloatCurve'], DI,
          curve(alpha))
    m.add('Motes', UPDATE, MOD + 'Update/Size/ScaleSpriteSize.ScaleSpriteSize')
    m.put('Motes', UPDATE, 'ScaleSpriteSize', 'Uniform Curve Sprite Scale', DI,
          curve(grow))
    m.renderer('Motes', {
        'Material': material,
        'bCastShadows': False,
        'SortMode': 'ViewDepth',
        'Alignment': 'Unaligned',
        'FacingMode': 'FaceCamera',
    })
    m.settle()
    m.save()
    return m


# SOMETHING IS HAPPENING TO THE BODY. A slow column clinging to the figure and
# drifting up off it: fire, rot and withering all read this way and differ only
# in colour. Deliberately thin -- twelve a second, not fifty -- because this is
# meant to be readable on a citizen standing in a market, not a bonfire.
mark('NS_MarkAura', 12.0, 1.30, 26.0, 46.0, 34.0, 1.4, 9.0,
     [(0.0, 0.55), (0.45, 1.15), (1.0, 0.3)], EMBER, 17.0,
     [(0.0, 0.0), (0.25, 0.85), (0.7, 0.7), (1.0, 0.0)])
# SOMETHING IS HOLDING THE BODY IN PLACE. Flat and low, barely moving, sitting
# round the feet: being rooted and being stilled are the same picture and the
# one thing worth drawing about either is that it is at the GROUND, which is
# what says the citizen is not going anywhere rather than that they are ill.
mark('NS_MarkGround', 9.0, 1.60, 14.0, 90.0, 4.0, 2.6, 11.0,
     [(0.0, 0.7), (0.5, 1.2), (1.0, 0.45)], SMOKE, 30.0,
     [(0.0, 0.0), (0.3, 0.7), (0.75, 0.6), (1.0, 0.0)])

print('four rites and two marks built. NOW RUN apply.py')
