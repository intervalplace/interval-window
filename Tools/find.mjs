// WHERE IN THE WORLD A KIND OF THING IS.
//
// `around.mjs` answers "what is within reach"; this answers "where is the
// nearest stall / ossuary / oak", which is the other half of playing a world
// you cannot see all of. Nothing here acts.
//
//   find.sh stall            -- every node whose type or kind contains 'stall'
//   find.sh oak 6            -- and only the six nearest
import { WebSocket } from 'ws'
const WANT = (process.argv[2] || '').toLowerCase()
const LIMIT = Number(process.argv[3] || 12)
const ws = new WebSocket('ws://127.0.0.1:7777')
const pad = (s, n) => String(s).padEnd(n).slice(0, n)
ws.on('message', (d) => {
  const f = JSON.parse(d.toString())
  if (!f.me) return
  const me = f.me
  const away = (o) => Math.max(Math.abs(o.x - me.x), Math.abs(o.y - me.y))
  const hits = []
  const sweep = (bag, what) => {
    for (const [id, o] of Object.entries(bag || {})) {
      const word = `${o.type ?? ''}.${o.kind ?? ''}`.toLowerCase()
      if (!WANT || word.includes(WANT) || id.toLowerCase().includes(WANT)) {
        hits.push([away(o), what, o.kind ? `${o.type}.${o.kind}` : o.type, id, `${o.x},${o.y}`])
      }
    }
  }
  sweep(f.nodes, 'node'); sweep(f.mobs, 'mob')
  hits.sort((a, b) => a[0] - b[0])
  console.log(`ME ${me.x},${me.y}: ${hits.length} matching "${WANT}" in the whole world:`)
  for (const h of hits.slice(0, LIMIT))
    console.log(`  ${String(h[0]).padStart(4)} tiles  ${pad(h[1], 5)} ${pad(h[2], 24)} ${pad(h[3], 26)} @${h[4]}`)
  process.exit(0)
})
ws.on('error', (e) => { console.error(e.message); process.exit(1) })
setTimeout(() => { console.error('no frame in 20s'); process.exit(1) }, 20000)
