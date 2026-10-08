// WHAT THE WORLD SAYS ABOUT THIS CITIZEN, for scripts that cannot read a screen.
// One frame, as JSON, and out.
import { WebSocket } from 'ws'
let hello = null
const w = new WebSocket('ws://127.0.0.1:7777')
const done = (o) => { try { w.close() } catch {} ; console.log(JSON.stringify(o)); process.exit(0) }
w.on('message', (d) => {
  const m = JSON.parse(d)
  if (m.k === 'hello') { hello = m; return }
  if (m.k !== 'frame' || !m.me || !hello) return
  const c = m.ceiling || {}
  // AND WHAT EACH THING IN THE PACK OFFERS, so a script can work out which
  // line of a menu it wants. `drop` is always the last line -- the window
  // sorts it there deliberately, so that a left click never throws away the
  // sword somebody just bought. A script that assumed "the first line is
  // drop" swept a pack of logs and fletched four bows, which is funny once.
  //
  // One verb is one line now, including `fletch`: it used to expand into a
  // row per make, and the whole reason it no longer does is that four rows
  // of fletching crowded everything else out. Counting it the old way here
  // would put `drop` three lines below where it is.
  const affords = hello?.itemAffords ?? {}
  const lines = (item) => (item ? (affords[item] ?? []).length : 0)
  done({
    x: m.me.x, y: m.me.y, gold: m.me.gold,
    dropRow: (m.me.inventory || []).map((s) => (s ? lines(s.item) - 1 : -1)),
    weapon: m.me.equipment?.weapon?.item ?? m.me.equipment?.weapon ?? null,
    pack: (m.me.inventory || []).map((s) => (s ? s.item : null)),
    woodcraft: m.me.skills?.woodcraft ?? 0,
    left: c.stoodDown ? 0 : Math.round((c.left || 0) / 60),
    stoodDown: !!c.stoodDown,
    place: m.place || '',
  })
})
setTimeout(() => done({ error: 'no frame' }), 12000)
