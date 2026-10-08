// WATCH THE WORLD'S ANSWER, interval by interval.
//
// The world says NOTHING when it declines a deed. The only trace is that
// `lastInput` never advances to the tick the deed was filed at, and that is
// invisible in any single reading -- you have to watch it across the two or
// three intervals a deed takes to be signed, carried and applied.
//
// Every hard thing found this session was found with some version of this, so
// it stops being retyped each time: the buy that vanished inside the bridge,
// the fletch that was refused for no reason anybody could name, the walks the
// ridge was eating, and the seven arrows that went into a corpse.
//
//   watchme.sh [intervals]      then file a deed in another shell
//
// `lastInput` moving to the current tick is the world saying yes. It staying
// put while the tick advances is the world saying no, and saying it the only
// way it ever does.
import pkg from './node_modules/ws/index.js'; const { WebSocket } = pkg
const N = Number(process.argv[2]) || 14
const ws = new WebSocket('ws://127.0.0.1:7777')
let seen = 0
ws.on('message', (d) => {
  const f = JSON.parse(d.toString())
  if (f.k === 'refused') { console.log('REFUSED BY THE BRIDGE: ' + JSON.stringify(f)); return }
  if (!f.me) return
  const me = f.me
  const pack = (me.inventory || []).map((s, i) => s ? `${i}:${s.item}x${s.qty}` : null)
                                   .filter(Boolean).join(' ')
  const took = me.lastInput === f.tick ? '  <- the world took it' : ''
  console.log(`t${f.tick} lastInput ${me.lastInput} ${String(me.x)},${me.y}`
    + ` hp ${me.hp} gold ${me.gold} ${me.action ? me.action.type : '-'} | ${pack}${took}`)
  if (++seen >= N) process.exit(0)
})
ws.on('error', (e) => { console.error(e.message); process.exit(1) })
setTimeout(() => process.exit(0), (N + 8) * 1000)
