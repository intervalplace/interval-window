// HOW MUCH OF THE DAY IS LEFT, for scripts that need to know.
// The window draws it; this is for the ones that cannot read a screen.
import { WebSocket } from 'ws'
const w = new WebSocket('ws://127.0.0.1:7777')
const done = (s) => { try { w.close() } catch {} ; console.log(s); process.exit(0) }
w.on('message', (d) => {
  const m = JSON.parse(d)
  if (m.k !== 'frame') return
  const c = m.ceiling || {}
  done(c.stoodDown ? 'stood down' : String(Math.round((c.left || 0) / 60)))
})
setTimeout(() => done('?'), 12000)
