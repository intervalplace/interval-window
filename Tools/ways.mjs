// WHERE THE RIVERS CAN BE CROSSED, which is not a thing the map can see.
//
// The map reads terrain chunks and draws what is within about ten tiles. A
// river is two hundred tiles long and its crossings are SCARCE AND NAMED --
// five on the whole island -- so a citizen standing on a bank has no way to
// learn whether the ford is eight tiles upstream or ninety downstream, and
// route-finding at that range is not something a ten-tile window can do.
//
// This asks the generator, which knows. It is the same trick the map now uses
// for the ridge: the world's own geography, read directly, rather than
// inferred from the little of it that happens to be in frame.
//
//   ways.sh            -> every crossing, nearest first
import pkg from './node_modules/ws/index.js'; const { WebSocket } = pkg
import * as W from './worldgen-expanse7.mjs'

const ws = new WebSocket('ws://127.0.0.1:7777')
let land = null
ws.on('message', (d) => {
  const f = JSON.parse(d.toString())
  if (f.k === 'hello') {
    const g = f.genesis || {}
    if (g.worldW && g.worldH) land = { worldW: g.worldW, worldH: g.worldH }
    return
  }
  if (!f.me || !land) return
  const me = f.me
  const away = (o) => Math.max(Math.abs(o.x - me.x), Math.abs(o.y - me.y))
  const ways = W.bridgesOf(land).slice()
  ways.sort((a, b) => away(a) - away(b))
  console.log(`ME ${me.x},${me.y}: the island's crossings, nearest first:`)
  for (const w of ways) {
    const dx = w.x - me.x, dy = w.y - me.y
    const bearing = (dy < 0 ? 'N' : dy > 0 ? 'S' : '') + (dx < 0 ? 'W' : dx > 0 ? 'E' : '')
    console.log(`  ${String(away(w)).padStart(4)} tiles  ${bearing.padEnd(3)} ${w.name.padEnd(24)} @${w.x},${w.y}`)
  }
  // And the two gaps in the spine, which bar the way east exactly as a river
  // bars the way north and are just as invisible to a ten-tile map.
  if (W.passesOf) {
    const rows = W.passesOf(land)
    console.log(`  the ridge is crossed only at rows ${rows.join(' and ')}` +
                ` (x about ${W.ridgeX ? W.ridgeX(land, rows[0]) : '?'})`)
  }
  process.exit(0)
})
ws.on('error', (e) => { console.error(e.message); process.exit(1) })
setTimeout(() => { console.error('no frame in 20s'); process.exit(1) }, 20000)
