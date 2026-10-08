// WHAT IS NEAR THE CITIZEN, in the world's own words.
//
// Every deed names a thing by its id -- `gather plan-anchor-402`, not "the
// tree over there" -- so playing this world from outside needs a way to ask
// what is within reach and what it is called. Nothing here acts; it reads one
// frame and prints it.
//
//   around.sh [radius]
import { WebSocket } from 'ws'
const R = Number(process.argv[2] || 12)
const ws = new WebSocket('ws://127.0.0.1:7777')
const pad = (s, n) => String(s).padEnd(n).slice(0, n)
ws.on('message', (d) => {
  const f = JSON.parse(d.toString())
  if (!f.me) return
  const me = f.me
  const away = (o) => Math.max(Math.abs(o.x - me.x), Math.abs(o.y - me.y))
  const pack = (me.inventory || []).map((s, i) => s ? `${i}:${s.item}×${s.qty}` : null).filter(Boolean)
  const worn = Object.entries(me.equipment || {}).filter(([, v]) => v).map(([k, v]) => `${k}:${v.item ?? v}`)
  console.log(`ME ${me.x},${me.y}  hp ${me.hp}  gold ${me.gold}  book ${me.book ?? 'common'}  ${me.action ? (me.action.type + (me.action.remaining !== undefined ? '+' + me.action.remaining : '')) : 'idle'}`)
  console.log(`   pack: ${pack.join(' ') || 'empty'}`)
  console.log(`   worn: ${worn.join(' ') || 'nothing'}`)
  const rows = []
  // A CORPSE LOOKS EXACTLY LIKE A TARGET. A killed mob stays in the frame
  // until it respawns -- `hp` at or below zero and a `respawnAt` in the future
  // -- and listing it with nothing else said sent seven arrows into a body
  // that was already dead, every one of them refused. The hp is the only way
  // to tell, so the hp is shown.
  const state = (o) => {
    if (o.hp === undefined) return ''
    return o.hp <= 0 ? '  DEAD' : `  hp ${o.hp}`
  }
  const add = (what, id, o, name) => { if (away(o) <= R) rows.push([away(o), what, name, id, `${o.x},${o.y}`, state(o)]) }
  for (const [id, n] of Object.entries(f.nodes || {})) add('node', id, n, n.kind ? `${n.type}.${n.kind}` : n.type)
  for (const [id, m] of Object.entries(f.mobs || {})) add('mob', id, m, m.kind ?? m.type)
  for (const [id, p] of Object.entries(f.players || {})) add('folk', id, p, p.name ?? id.slice(0, 8))
  rows.sort((a, b) => a[0] - b[0])
  // The walls and ramparts of a town are hundreds of identical rows and
  // nothing anybody acts on; counted, not listed.
  const dull = new Set(['wall', 'rampart', 'floor'])
  const shown = rows.filter((r) => !dull.has(r[2]))
  const hidden = rows.length - shown.length
  console.log(`${rows.length} within ${R} tiles (${hidden} wall/rampart tiles not listed):`)
  // ALL OF THEM, NOT THE FIRST FORTY-FOUR.
  //
  // This printed `shown.slice(0, 44)` with no word about the rest, and at a
  // wide radius that is most of what is standing there. Fifty hedges round the
  // goblin pound were cut off the bottom of the list, which sent an hour into
  // asking what the large green things in the picture could possibly be --
  // while the answer sat in the frame, unprinted. A list that silently stops
  // is worse than a short one.
  if (shown.length > 60) {
    console.log(`  (${shown.length} rows; the tally first)`)
    const tally = {}
    for (const r of shown) tally[r[2]] = (tally[r[2]] || 0) + 1
    for (const [k, c] of Object.entries(tally).sort((a, b) => b[1] - a[1]))
      console.log(`  ${String(c).padStart(4)}  ${k}`)
  }
  for (const r of shown.slice(0, 60))
    console.log(`  ${String(r[0]).padStart(3)}  ${pad(r[1], 5)} ${pad(r[2], 22)} ${pad(r[3], 24)} @${r[4]}${r[5] ?? ''}`)
  process.exit(0)
})
ws.on('error', (e) => { console.error(e.message); process.exit(1) })
setTimeout(() => { console.error('no frame in 20s'); process.exit(1) }, 20000)
