// WHAT THE GROUND ACTUALLY IS, in the world's own words.
//
// The terrain chunk arrives as a base64 block of BYTES, and a byte is only a
// number until something names it. The names are the bridge's `TILE_NAMES`,
// indexed by the code -- 24 is `downs`, 7 is `chalk`, 12 is `river`. Decoding
// a chunk by hand is what proved a citizen stranded beside the South Pass was
// standing on perfectly walkable downland, which is what sent the search to
// the ridge PREDICATE instead of to the ground.
//
//   soil.sh [x0 y0 w h]      default: a 15x15 square around the citizen
//
// The map draws glyphs and is for routing. This prints the word, and is for
// answering "why will the world not let me stand there".
import pkg from './node_modules/ws/index.js'; const { WebSocket } = pkg
const A = process.argv.slice(2).map(Number)
const ws = new WebSocket('ws://127.0.0.1:7777')
let names = null, asked = false
ws.on('message', (d) => {
  const f = JSON.parse(d.toString())
  if (f.k === 'hello') { names = f.tiles || null; return }
  if (f.k === 'terrain') {
    const t = Buffer.from(f.tiles, 'base64')
    const w = f.w + f.skirt * 2
    for (let y = 0; y < f.h + f.skirt * 2; y++) {
      let row = ''
      for (let x = 0; x < w; x++) {
        const n = (names && names[t[y * w + x]]) || String(t[y * w + x])
        row += n.slice(0, 5).padEnd(6)
      }
      console.log(String(f.y0 - f.skirt + y).padStart(4) + ' ' + row)
    }
    console.log('     x from ' + (f.x0 - f.skirt))
    process.exit(0)
  }
  if (!f.me || asked) return
  asked = true
  const [x0, y0, w, h] = A.length === 4 ? A : [f.me.x - 7, f.me.y - 7, 15, 15]
  console.log(`ME ${f.me.x},${f.me.y}: the ground from ${x0},${y0}:`)
  ws.send(JSON.stringify({ k: 'terrain', x0, y0, w, h, skirt: 0 }))
})
ws.on('error', (e) => { console.error(e.message); process.exit(1) })
setTimeout(() => { console.error('no frame in 20s'); process.exit(1) }, 20000)
