// PICK A FIGHT, AND KNOW WHEN TO STOP.
//
// Combat here is not a button: a beast is struck from ADJACENT (inReach uses
// the weapon's reach, and a dagger's is one), it strikes back every tick, and
// the citizen has one pool of hit points and no healer. So this walks in,
// swings, and watches BOTH bars -- and breaks off on the citizen's hp rather
// than on the beast's, because a fight you win at four hit points is a fight
// you lost the next time something noticed you.
//
//   fight.mjs <mobId> [style] [floor]
import pkg from '../../interval-bridge/node_modules/ws/index.js'; const { WebSocket } = pkg
import { appendFileSync } from 'fs'
import { execFile } from 'child_process'
import { fileURLToPath } from 'url'
import { dirname } from 'path'
const SP = dirname(fileURLToPath(import.meta.url))
const ID = process.argv[2]
const STYLE = process.argv[3] || 'even'
const FLOOR = Number(process.argv[4] || 28)   // break off at this many hp
const CMD = '/private/tmp/claude-501/-Users-matsjulner-Documents-Unreal-Projects-interval/d4aebce9-c39a-4f8e-86ec-ab2848a159a1/scratchpad/play.cmd'
const file = (line) => appendFileSync(CMD, line + '\n')

const ws = new WebSocket('ws://127.0.0.1:7777')
let swungAt = -99, startHp = null, n = 0, closing = false
ws.on('message', (d) => {
  let f; try { f = JSON.parse(d.toString()) } catch { return }
  if (!f.me) return
  const me = f.me, m = (f.mobs || {})[ID]
  if (startHp === null) startHp = me.hp
  if (!m || m.hp <= 0) {
    console.log(`the ${m ? m.kind ?? m.type : 'beast'} is down. citizen hp ${me.hp} (started ${startHp})`)
    process.exit(0)
  }
  const gap = Math.max(Math.abs(m.x - me.x), Math.abs(m.y - me.y))
  if (me.hp <= FLOOR) {
    console.log(`BREAKING OFF at ${me.hp} hp, ${m.kind ?? m.type} still has ${m.hp}`)
    process.exit(2)
  }
  if (gap > 1) {
    // CLOSING IS A JOURNEY, NOT A NUDGE.
    //
    // This used to file a walk straight at the beast, which works in a field
    // and fails at a pen: twenty runs went into the same refused step with a
    // fence between us, because a straight line is not a route. It hands the
    // closing to go.sh, which reads the terrain and the walls and comes round.
    //
    // Onto a tile BESIDE it, never onto it -- a living beast holds its tile,
    // and walking into one is refused by the world rather than being an attack.
    if (!closing && f.tick - swungAt > 3) {
      swungAt = f.tick
      const tx = m.x - Math.sign(m.x - me.x), ty = m.y - Math.sign(m.y - me.y)
      console.log(`t${f.tick} closing: ${gap} tiles to ${m.kind ?? m.type} -> route to ${tx},${ty}`)
      closing = true
      execFile('bash', [SP + '/go.sh', String(tx), String(ty), '8'], { timeout: 120000 },
        (err, out) => {
          const last = String(out || '').trim().split('\n').pop()
          if (last) console.log('  ' + last)
          closing = false
        })
    }
    return
  }
  // Adjacent. A dagger swings every other interval; filing faster only
  // queues deeds the world will refuse.
  if (f.tick - swungAt >= 2) {
    swungAt = f.tick
    console.log(`t${f.tick} strike: ${m.kind ?? m.type} hp ${m.hp}, me hp ${me.hp}`)
    file(`attack ${ID} ${STYLE}`)
  }
  if (++n > 400) { console.log('fight ran long, standing off'); process.exit(3) }
})
ws.on('error', (e) => { console.error(e.message); process.exit(1) })
setTimeout(() => { console.log('nothing happened in three minutes'); process.exit(4) }, 180000)
