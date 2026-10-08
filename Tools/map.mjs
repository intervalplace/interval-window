// A LOCAL MAP, because "that way is blocked" is not a route.
//
// around.sh counts the walls and refuses to list them -- rightly, they are
// hundreds of identical rows -- but a town is walls, and a stall standing three
// tiles away with a rampart in between is unreachable in a way no list shows.
// This draws what is actually in the way, and a route through it.
//
//   map.sh [radius] [targetX targetY]
import pkg from '../../interval-bridge/node_modules/ws/index.js'; const { WebSocket } = pkg

// THE RIDGE IS NOT A TERRAIN CODE, AND THE MAP COULD NOT SEE IT.
//
// The island's spine is a PREDICATE -- `onRidge` in the world generator -- not
// a ground the terrain chunk names. The tiles along it come back as ordinary
// `downs`, so this map called them open and routed straight through a wall
// that the world refuses every step of. That is what stranded a citizen beside
// the South Pass: sixty runs, every one of them a refused step into the same
// five columns of rock, and nothing anywhere saying "there is a mountain
// there".
//
// Imported softly. The ridge belongs to expanse7; a window onto some other
// world should lose the ridge, not fall over.
let onRidge = null
try {
  ({ onRidge } = await import('../../interval-bridge/worldgen-expanse7.mjs'))
} catch { onRidge = null }
let land = null
const R = Number(process.argv[2] || 10)
const TX = process.argv[3] !== undefined ? Number(process.argv[3]) : null
const TY = process.argv[4] !== undefined ? Number(process.argv[4]) : null

// WHAT BARS A TILE, taken from the world instead of guessed at.
//
// The first version listed what it thought was impassable and was wrong in
// BOTH directions, which is the usual result of guessing. The engine's rule
// is the other way round: blockingNodeAt() bars every node type EXCEPT an
// explicit walkable set, so the list to copy is the short one.
//
// `plot` was the expensive mistake. Ploughed ground is walked over -- you
// stand in one furrow to work the next -- and the engine says so in a long
// note about the founding where plots DID block: 1,269 of the island's 1,370
// field plots could not be reached by anybody, because any shape two tiles
// thick has an unreachable middle. Treating them as walls here meant routing
// around every field on the island for no reason.
//
// Landmarks, by contrast, really do bar the way. There are thousands of them
// scattered about, so paths through open country genuinely wiggle; that is
// the world, not the map.
// Terrain that bars the way regardless of what stands on it. The engine asks
// terrainBlocked() before it asks about nodes at all, and a finished span is
// the one thing that makes water walkable -- which is why `span` appears in
// the walkable-built set below.
// WHAT THE WORLD ACTUALLY BARS, WHICH IS THREE THINGS.
//
// `blockedAt` in the generator is the whole of it: water without a ford, the
// RIDGE without a road, and the BARROW without a road. That is all. Nothing
// else in the world stops a citizen walking.
//
// This set also held `crags`, `mountain` and `cave` -- three ground NAMES that
// the world treats as ordinary country you cross slowly (`BIOME_COST4` prices
// crags at 22 against the heartlands' 10; a cost, not a wall). The east of the
// island IS crags, so the window walled off a third of the world and answered
// "out of sight or walled in" for every route into it. Found by walking a
// citizen through the North Pass -- which is open, the generator shuts only
// the South one -- and then being unable to route a single tile further.
//
// The ridge is not here because it is not a ground either: it is a predicate,
// consulted separately below.
const IMPASSABLE = new Set(['sea', 'river'])

const WALKABLE_BUILT = new Set(['smokerack', 'brewpot', 'watchfire', 'fire',
  'market', 'cart', 'dedication', 'span', 'plot'])
const GLYPH = { wall: '#', rampart: '#', hedge: '"', fence: 'f', vault: 'B',
  store: 'S', anvil: 'A', smith: 's', keeper: 'k', guard: 'G', hearth: 'h',
  well: 'o', campfire: '*', signpost: 'i', landmark: '!', tree: 'T',
  rock: 'n', stall: '$', banner: 'b', door: '+' }

const ws = new WebSocket('ws://127.0.0.1:7777')
let tileNames = null
let terrain = null   // {x0,y0,w,h,skirt,tiles}
ws.on('message', (d) => {
  const f = JSON.parse(d.toString())
  if (f.k === 'hello') {
    tileNames = f.tiles || null
    // The ridge predicate wants the island's size, which only `hello` carries.
    const g = f.genesis || {}
    if (g.worldW && g.worldH) land = { worldW: g.worldW, worldH: g.worldH }
    return
  }
  if (f.k === 'terrain') {
    terrain = { x0: f.x0, y0: f.y0, w: f.w, h: f.h, skirt: f.skirt,
                tiles: Buffer.from(f.tiles, 'base64') }
    draw(pending)
    return
  }
  if (!f.me) return
  pending = f
  // Ask for the ground under the map before drawing any of it.
  if (!terrain) {
    ws.send(JSON.stringify({ k: 'terrain', x0: f.me.x - R, y0: f.me.y - R,
                             w: R * 2 + 1, h: R * 2 + 1, skirt: 0 }))
    return
  }
  draw(f)
})
let pending = null
function terrainAt (x, y) {
  if (!terrain || !tileNames) return null
  const sw = terrain.w + terrain.skirt * 2
  const ix = x - (terrain.x0 - terrain.skirt), iy = y - (terrain.y0 - terrain.skirt)
  if (ix < 0 || iy < 0 || ix >= sw || iy >= terrain.h + terrain.skirt * 2) return null
  return tileNames[terrain.tiles[iy * sw + ix]] ?? null
}
function draw (f) {
  const me = f.me
  const blocked = new Map()   // "x,y" -> glyph
  for (const n of Object.values(f.nodes || {})) {
    const base = String(n.type || '').split('.')[0]
    if (!WALKABLE_BUILT.has(base)) blocked.set(`${n.x},${n.y}`, GLYPH[base] || '?')
  }
  // `^` MEANS A WALL, AND CRAGS ARE NOT ONE.
  //
  // Rough country was drawn with the same glyph as the ridge, so a map of the
  // eastern third of the island looked like a solid mountain from edge to
  // edge -- and read exactly like the thing the router refuses. It cost an
  // hour of asking why a citizen standing in open crags could not move. The
  // ridge keeps `^`, because the ridge really is a wall; ground you cross
  // slowly gets a mark of its own.
  const water = { sea: '~', river: '~', mountain: ',', crags: ',', cave: 'C' }
  const shut = (x, y) => {
    if (blocked.has(`${x},${y}`)) return true
    // The spine, which no terrain code names. See the note at the top.
    if (onRidge && land && onRidge(land, x, y)) return true
    const t = terrainAt(x, y)
    return t !== null && IMPASSABLE.has(t)
  }

  // Breadth-first, eight-way, over the tiles we can actually see.
  const route = (tx, ty) => {
    const key = (x, y) => `${x},${y}`
    const seen = new Map([[key(me.x, me.y), null]])
    let edge = [[me.x, me.y]]
    while (edge.length) {
      const next = []
      for (const [x, y] of edge) {
        if (x === tx && y === ty) {
          const path = []
          for (let k = key(x, y); k; k = seen.get(k)) path.unshift(k)
          return path
        }
        // NEIGHBOURS IN THE DIRECTION OF TRAVEL FIRST.
        //
        // Every eight-way path of the same length is equally short, so a
        // breadth-first search returns whichever it happened to reach first
        // -- and in open country that was a zigzag. It walked fine, but a
        // `walk` is ONE STRAIGHT RUN, so a zigzag of eleven steps is six
        // separate deeds where a straight line is one. Crossing the island
        // went at half the speed the world allows for no reason but the
        // order of a loop. Stepping toward the target first makes the paths
        // straight, and straight paths make long runs.
        const toward = []
        for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++)
          if (dx || dy) toward.push([dx, dy])
        toward.sort((a, b) => {
          const score = ([ex, ey]) =>
            -(ex * Math.sign(tx - x) + ey * Math.sign(ty - y))
          return score(a) - score(b)
        })
        for (const [dx, dy] of toward) {
          const nx = x + dx, ny = y + dy
          if (Math.abs(nx - me.x) > R || Math.abs(ny - me.y) > R) continue
          if (seen.has(key(nx, ny))) continue
          // The target itself may be a thing you walk UP TO rather than
          // onto -- a stall, a keeper. But a waypoint standing on a signpost
          // is a route that ends in a wall, so ADJACENT counts as arrived
          // when the target is occupied.
          if (shut(nx, ny) && !(nx === tx && ny === ty)) continue
          seen.set(key(nx, ny), key(x, y)); next.push([nx, ny])
        }

      }
      edge = next
    }
    return null
  }

  // THE IDEAL PATH FIRST, WHICH IS TWO RUNS AND NOT TWENTY-FIVE.
  //
  // Breadth-first over eight neighbours returns A shortest path, and for any
  // target that is not on a ray or a perfect diagonal that path is a
  // STAIRCASE -- alternating diagonal and straight steps. It has the right
  // length and it is the wrong shape: a `walk` is one straight run, so a
  // staircase of fifty-eight steps costs twenty-five deeds where the same
  // fifty-eight steps, grouped, cost two.
  //
  // The natural eight-way route is diagonal until one axis is used up, then
  // straight along the other. That is what this tries; the search stays as
  // the fallback for when something is actually in the way, which is what a
  // search is for.
  const ideal = (tx, ty) => {
    const legs = []
    let x = me.x, y = me.y
    const step = (dx, dy, n) => {
      for (let k = 0; k < n; k++) {
        x += dx; y += dy
        if (shut(x, y) && !(x === tx && y === ty)) return false
      }
      if (n > 0) legs.push([x, y])
      return true
    }
    const dx = Math.sign(tx - me.x), dy = Math.sign(ty - me.y)
    const diag = Math.min(Math.abs(tx - me.x), Math.abs(ty - me.y))
    if (!step(dx, dy, diag)) return null
    const restX = tx - x, restY = ty - y
    if (!step(Math.sign(restX), Math.sign(restY), Math.abs(restX) + Math.abs(restY))) return null
    return (x === tx && y === ty) ? legs : null
  }

  let straight = (TX !== null && TY !== null) ? ideal(TX, TY) : null
  const path = (TX !== null && TY !== null) ? route(TX, TY) : null
  const onPath = new Set(path || [])
  console.log(`ME ${me.x},${me.y}   # wall  ~ water  ^ ridge  , rough  " hedge  f fence  $ stall  k keeper  · path  @ me  X target`)
  for (let y = me.y - R; y <= me.y + R; y++) {
    let row = String(y).padStart(4) + ' '
    for (let x = me.x - R; x <= me.x + R; x++) {
      const k = `${x},${y}`
      row += (x === me.x && y === me.y) ? '@'
        : (x === TX && y === TY) ? 'X'
        : onPath.has(k) ? '·'
        : blocked.get(k)
          || ((onRidge && land && onRidge(land, x, y)) ? '^' : null)
          || water[terrainAt(x, y)] || '.'
    }
    console.log(row)
  }
  if (TX !== null) {
    if (!path) console.log(`\nNO ROUTE to ${TX},${TY} within ${R} tiles of sight.`)
    else {
      const steps = path.slice(1).map((k) => k)
      console.log(`\nroute in ${steps.length} steps: ${steps.join(' -> ')}`)
      // The legs a `walk` can actually take: straight runs, one per direction change.
      const legs = []
      let px = me.x, py = me.y, dx = 0, dy = 0
      for (const k of steps) {
        const [x, y] = k.split(',').map(Number)
        const ndx = Math.sign(x - px), ndy = Math.sign(y - py)
        if (ndx !== dx || ndy !== dy) { legs.push([x, y]); dx = ndx; dy = ndy }
        else legs[legs.length - 1] = [x, y]
        px = x; py = y
      }
      // PULL THE STAIRCASE STRAIGHT.
      //
      // Even when the direct route is blocked, the search's answer is mostly
      // staircase -- and a staircase is only expensive because each change of
      // direction is another deed. So walk the path and, from each point,
      // reach as far along it as ONE straight run can actually go. What is
      // left is the same route in a handful of runs instead of dozens.
      //
      // This is the ordinary "string pulling" a path gets before anything
      // walks it, and it matters more here than in most places: the cost of a
      // corner is not a few wasted frames, it is a whole deed against a
      // citizen's daily allowance and a second of the world's time.
      const pull = (pts) => {
        const clear = (ax, ay, bx, by) => {
          const dx = Math.sign(bx - ax), dy = Math.sign(by - ay)
          const n = Math.max(Math.abs(bx - ax), Math.abs(by - ay))
          // A straight run is ONE ray: it must be axis-aligned or a true
          // diagonal, or the world cannot express it as (dx, dy, steps).
          if (Math.abs(bx - ax) !== Math.abs(by - ay) && bx !== ax && by !== ay) return false
          let x = ax, y = ay
          for (let k = 0; k < n; k++) {
            x += dx; y += dy
            if (shut(x, y) && !(x === TX && y === TY)) return false
          }
          return true
        }
        const out = []
        let ax = me.x, ay = me.y, i = 0
        while (i < pts.length) {
          let best = i
          for (let j = pts.length - 1; j >= i; j--) {
            const [bx, by] = pts[j].split(',').map(Number)
            if (clear(ax, ay, bx, by)) { best = j; break }
          }
          const [bx, by] = pts[best].split(',').map(Number)
          out.push([bx, by]); ax = bx; ay = by; i = best + 1
        }
        return out
      }
      const use = straight ?? pull(steps)
      console.log(`straight runs: ${use.map(([x, y]) => `walk ${x} ${y}`).join('  |  ')}`)
    }
  }
  process.exit(0)
}
ws.on('error', (e) => { console.error(e.message); process.exit(1) })
setTimeout(() => { console.error('no frame in 20s'); process.exit(1) }, 20000)
