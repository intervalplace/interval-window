// WHERE THE ISLAND CONTRADICTS ITSELF.
//
// A lot of this world is hand drawn -- the holdings are literal rows of
// characters with a legend, the copses and mires are a list of named features
// with a centre and radii -- and hand-drawn things collide. Two steadings laid
// a few tiles apart put their fields through each other and read on the ground
// as one enormous field; a copse lands half in a river; a farmstead's hedge
// runs through a road. None of that is visible from inside the generator,
// because the generator is drawing one feature at a time and each one is
// individually correct.
//
// So this looks at the WHOLE island at once and reports every place two
// authored things disagree. It is a report and nothing else: it changes no
// world, writes no fix and makes no decision about which of two overlapping
// fields is the wrong one. That judgement is the author's, and the point of
// the report is to put it in front of them instead of making them find it by
// walking three hundred tiles.
//
//   node conflicts.mjs            -- the report
//   node conflicts.mjs --json     -- the same, machine readable
//   node conflicts.mjs --rebuild  -- ignore the cache and generate again
//
// It runs from the bridge's directory because that is where the generator and
// the engine live. See Tools/conflicts.sh.
import fs from 'fs'
import { createRequire } from 'module'
import { buildWorld, generatorFor } from './worldgen-any.mjs'
const require = createRequire(import.meta.url)

const ARGS = process.argv.slice(2)
const AS_JSON = ARGS.includes('--json')
const CACHE = '/tmp/interval-world.json'

const PILLAR = 'https://interval.place'
const getJson = async (p) => (await fetch(PILLAR + p)).json()

// ---- the island, built once and kept ----
//
// Generating is two minutes of work and perfectly deterministic, so a cache
// keyed on the genesis seed costs nothing and makes iterating on the report
// bearable. It is thrown away the moment the founding changes, because a
// report about a different island is worse than no report.
async function island () {
  const g = await getJson('/api/genesis')
  const G = g.genesis
  const seats = (await getJson('/api/settlements').catch(() => ({ settlements: [] }))).settlements ?? []
  const key = `${G.worldGenerator}|${G.genesisSeed}|${G.worldW}x${G.worldH}`
  if (!ARGS.includes('--rebuild') && fs.existsSync(CACHE)) {
    const held = JSON.parse(fs.readFileSync(CACHE, 'utf8'))
    if (held.key === key) return { G, seats, nodes: held.nodes, holds: held.holds }
  }
  process.stderr.write('generating the island (about two minutes)...\n')
  const w = buildWorld(G)
  const gen = generatorFor(G)
  const holds = gen.holdingsOf(G)
  const nodes = Object.entries(w.nodes).map(([id, n]) =>
    ({ id, type: n.type, kind: n.kind ?? '', x: n.x, y: n.y }))
  fs.writeFileSync(CACHE, JSON.stringify({ key, nodes, holds }))
  return { G, seats, nodes, holds }
}

const rect = (r) => ({ x0: r.x0 ?? (r.x - (r.w >> 1)), y0: r.y0 ?? (r.y - (r.h >> 1)),
                       w: r.w, h: r.h })
const overlap = (a, b) => {
  const A = rect(a), B = rect(b)
  const x = Math.min(A.x0 + A.w, B.x0 + B.w) - Math.max(A.x0, B.x0)
  const y = Math.min(A.y0 + A.h, B.y0 + B.h) - Math.max(A.y0, B.y0)
  return (x > 0 && y > 0) ? x * y : 0
}

const main = async () => {
  const { G, seats, nodes, holds } = await island()
  const gen = generatorFor(G)
  const found = []
  const say = (kind, where, text, extra = {}) =>
    found.push({ kind, x: where[0], y: where[1], text, ...extra })

  // ---- 1. TWO DRAWINGS THROUGH EACH OTHER ----
  //
  // The one the report exists for. Each holding owns a rectangle it drew
  // itself into; two rectangles that intersect are two farmsteads sharing
  // ground, and what that looks like from above is a field with no edge.
  for (let i = 0; i < holds.length; i++) {
    for (let j = i + 1; j < holds.length; j++) {
      const n = overlap(holds[i], holds[j])
      if (!n) continue
      say('holdings-overlap', [holds[i].x, holds[i].y],
        `${holds[i].name} (${holds[i].tag}) and ${holds[j].name} (${holds[j].tag}) share ${n} tiles`,
        { tiles: n, a: holds[i].id, b: holds[j].id })
    }
  }

  // ---- 2. A FARM INSIDE A TOWN ----
  for (const h of holds) {
    for (const s of seats) {
      const n = overlap(h, s)
      if (n) {
        say('holding-in-settlement', [h.x, h.y],
          `${h.name} stands ${n} tiles inside ${s.name}`, { tiles: n })
      }
    }
  }

  // ---- 3. TWO TOWNS THROUGH EACH OTHER ----
  for (let i = 0; i < seats.length; i++) {
    for (let j = i + 1; j < seats.length; j++) {
      const n = overlap(seats[i], seats[j])
      if (n) {
        say('settlements-overlap', [seats[i].x, seats[i].y],
          `${seats[i].name} and ${seats[j].name} share ${n} tiles`, { tiles: n })
      }
    }
  }

  // ---- 4. TWO THINGS STANDING ON ONE TILE ----
  //
  // The generator already says how many of these it resolved -- "4 node(s)
  // shared a tile; the drawn thing kept it" -- and never says WHERE, so
  // nobody can look at one and decide whether the right thing was kept.
  const byTile = new Map()
  for (const n of nodes) {
    const k = n.x + ',' + n.y
    if (!byTile.has(k)) byTile.set(k, [])
    byTile.get(k).push(n)
  }
  for (const [k, list] of byTile) {
    if (list.length < 2) continue
    const [x, y] = k.split(',').map(Number)
    say('stacked', [x, y],
      list.map((n) => n.kind || n.type).join(' + ') + ' on one tile',
      { ids: list.map((n) => n.id) })
  }

  // ---- 5. STANDING IN WATER, OR IN A HILL ----
  //
  // A thing on ground nobody can reach is a thing nobody can use, and it is
  // the kind of fault that survives for ever because it is invisible from
  // every path a citizen would walk.
  // Some things BELONG in water and reporting them is noise that buries the
  // one that does not: the first run of this found sixteen, and thirteen were
  // fishing spots doing their job.
  const AT_HOME_IN_WATER = new Set(['fishing-spot', 'deep-fish-spot', 'eel-spot',
    'gibbet-shoal', 'quay', 'ford', 'bridge', 'jetty', 'weir', 'mill-wheel'])
  for (const n of nodes) {
    if (AT_HOME_IN_WATER.has(n.type)) continue
    if (gen.isWater(G, n.x, n.y)) {
      say('in-water', [n.x, n.y], `${n.kind || n.type} stands in water`, { id: n.id })
    }
  }

  // ---- 6. A FIELD WITH NO EDGE ----
  //
  // Two plots touching across a holding boundary. Each is correct; together
  // they are one field twice the size, which is exactly the thing that was
  // noticed -- "some things are placed halfway on top of eachother like 2
  // fields for example so they are like merged into one".
  const plotOf = new Map()
  for (const n of nodes) {
    if (n.type === 'plot') plotOf.set(n.x + ',' + n.y, n.id)
  }
  const hold_of = new Map()
  for (const h of holds) {
    for (let ry = 0; ry < h.h; ry++) for (let rx = 0; rx < h.w; rx++) {
      hold_of.set((h.x0 + rx) + ',' + (h.y0 + ry), h.id)
    }
  }
  const seen = new Set()
  for (const [k] of plotOf) {
    const [x, y] = k.split(',').map(Number)
    for (const [dx, dy] of [[1, 0], [0, 1]]) {
      const j = (x + dx) + ',' + (y + dy)
      if (!plotOf.has(j)) continue
      const a = hold_of.get(k), b = hold_of.get(j)
      if (!a || !b || a === b) continue
      const pair = a < b ? a + '|' + b : b + '|' + a
      if (seen.has(pair)) continue
      seen.add(pair)
      const A = holds.find((h) => h.id === a), B = holds.find((h) => h.id === b)
      say('fields-merged', [x, y],
        `${A.name}'s field runs straight into ${B.name}'s`, { a, b })
    }
  }

  // ---- 7. A WALL ACROSS A ROAD ----
  // INSIDE A TOWN A WALL MEETS PAVING EVERYWHERE, and calling each of those a
  // conflict drowned the report: two hundred and twenty-five hits, nearly all
  // of them a house standing correctly on a street. Only open country is
  // interesting, where a road is a road and a wall across it is a wall across
  // it.
  const BLOCKS = new Set(['wall', 'fence', 'hedge', 'palisade', 'railing'])
  const inTown = (x, y) => seats.some((s) =>
    Math.abs(x - s.x) <= (s.w >> 1) && Math.abs(y - s.y) <= (s.h >> 1))
  for (const n of nodes) {
    if (!BLOCKS.has(n.type)) continue
    if (inTown(n.x, n.y)) continue
    if (gen.onRoad && gen.onRoad(G, n.x, n.y)) {
      say('blocks-road', [n.x, n.y], `${n.kind || n.type} stands on the road`, { id: n.id })
    }
  }

  // ---- 8. AN ENCLOSURE WITH A HOLE IN IT ----
  //
  // THE ONE THAT MATCHES WHAT WAS ACTUALLY SEEN. A field reads as a field
  // because something runs all the way round it; a ring with one tile missing
  // reads as two fields that have merged, which is exactly the complaint --
  // "some things are placed halfway on top of eachother like 2 fields for
  // example so they are like merged into one".
  //
  // So: from every plot tile, walk outward through anything that is not a
  // fence, a hedge or a wall. If the walk reaches open country, the ring is
  // broken, and the tile it escaped through is the gap worth looking at.
  const shut = new Set()
  for (const n of nodes) {
    if (BLOCKS.has(n.type)) shut.add(n.x + ',' + n.y)
  }
  for (const h of holds) {
    const mine = []
    for (const n of nodes) {
      if (n.type !== 'plot') continue
      if (n.x < h.x0 || n.y < h.y0 || n.x >= h.x0 + h.w || n.y >= h.y0 + h.h) continue
      mine.push(n)
    }
    if (!mine.length) continue
    // A generous margin: a ring is only a ring if it holds within a couple of
    // tiles of the drawing that made it.
    const pad = 2
    const lo = [h.x0 - pad, h.y0 - pad], hi = [h.x0 + h.w + pad, h.y0 + h.h + pad]
    const seenT = new Set()
    const queue = mine.map((n) => [n.x, n.y])
    let leak = null
    while (queue.length && !leak) {
      const [x, y] = queue.pop()
      const k = x + ',' + y
      if (seenT.has(k)) continue
      seenT.add(k)
      if (x <= lo[0] || y <= lo[1] || x >= hi[0] || y >= hi[1]) { leak = [x, y]; break }
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = x + dx, ny = y + dy
        if (shut.has(nx + ',' + ny)) continue
        if (!seenT.has(nx + ',' + ny)) queue.push([nx, ny])
      }
    }
    if (leak) {
      say('enclosure-open', leak,
        `${h.name}'s field is not closed -- it runs out at ${leak[0]},${leak[1]}`,
        { hold: h.id })
    }
  }

  if (AS_JSON) {
    console.log(JSON.stringify({ world: G.worldW + 'x' + G.worldH, found }, null, 1))
    return
  }

  const order = ['holdings-overlap', 'fields-merged', 'enclosure-open',
                 'settlements-overlap', 'holding-in-settlement', 'stacked',
                 'in-water', 'blocks-road']
  const TITLE = {
    'holdings-overlap': 'TWO HOLDINGS DRAWN THROUGH EACH OTHER',
    'fields-merged': 'FIELDS THAT RUN INTO ONE ANOTHER',
    'settlements-overlap': 'TWO SETTLEMENTS SHARING GROUND',
    'holding-in-settlement': 'A HOLDING INSIDE A TOWN',
    'stacked': 'TWO THINGS ON ONE TILE',
    'in-water': 'STANDING IN WATER',
    'blocks-road': 'STANDING ON THE ROAD, IN OPEN COUNTRY',
    'enclosure-open': 'A FIELD THAT IS NOT CLOSED IN',
  }
  console.log(`\nthe island is ${G.worldW} by ${G.worldH}; ${nodes.length} things stand on it`)
  console.log(`${found.length} conflicts\n`)
  for (const kind of order) {
    const mine = found.filter((f) => f.kind === kind)
    if (!mine.length) continue
    console.log(`  ${TITLE[kind]}  (${mine.length})`)
    for (const f of mine.slice(0, 40)) {
      console.log(`    ${String(f.x).padStart(4)},${String(f.y).padEnd(4)}  ${f.text}`)
    }
    if (mine.length > 40) console.log(`    ... and ${mine.length - 40} more`)
    console.log('')
  }
}

main().catch((e) => { console.error(e); process.exit(1) })
