// EVERYTHING THE WORLD HAS A WORD FOR, OUT OF THE ENGINE ITSELF.
//
// `Tools/audit.py` used to read a file captured from a running world -- the
// node types and kinds that had been SEEN in a frame. That is a sample of a
// living world, not its vocabulary, and it quietly reported perfect coverage
// while fourteen node types had no row in the window at all. One of them was
// `cart`, which is what a dead hauler spills and which anybody may unload.
//
// The engine exports its own tables. They cannot be behind themselves, they
// cannot be a sample, and they change the day the world changes. Nothing else
// should ever be asked.
//
//   node Tools/scope.mjs > scope.json
import { createRequire } from 'module'
const require = createRequire(import.meta.url)
const e = require('../../interval-bridge/engine.js')

const list = (v) => Array.isArray(v) ? v
  : v instanceof Set ? [...v]
  : v && typeof v === 'object' ? Object.keys(v)
  : []

// THE KINDS ARE THE ONE THING THE ENGINE DOES NOT HAND OVER AS A LIST.
//
// A node's `kind` is a free string the generator chooses -- `landmark.cairn`,
// `wall.roofed`, `keeper.miller` -- and there is no table of them to read. So
// they are gathered from the two places that DO constrain them: the scenery
// words the validator accepts, and whatever a live world has actually seated.
// That is still a sample for the second half, and it is marked as such rather
// than presented as a vocabulary, which is the whole lesson here.
const out = {
  items: list(e.ITEMS).sort(),
  equippable: list(e.EQUIPPABLE).sort(),
  weapons: list(e.WEAPONS).sort(),
  armour: list(e.ARMOUR).sort(),
  twoHanded: list(e.TWO_HANDED).sort(),
  stackable: list(e.STACKABLE).sort(),
  smelted: list(e.SMELTED).sort(),
  nodeTypes: list(e.NODE_TYPES).sort(),
  keeperKinds: list(e.KEEPER_KINDS).sort(),
  stalls: list(e.STALL_SELLS).sort(),
  mobs: list(e.MOB_STATS).sort(),
  recipes: list(e.RECIPES).sort(),
  prices: list(e.PRICES).sort(),
  skills: list(e.SKILLS).sort(),
  callings: list(e.CALLINGS).sort(),
  callingNames: list(e.CALLING_NAMES).sort(),
  equipSlots: list(e.EQUIP_SLOTS).sort(),
  styles: list(e.STYLES).sort(),
  gatherTools: list(e.GATHER_TOOLS).sort(),
  nodeYield: list(e.NODE_YIELD).sort(),
  nodeGate: list(e.NODE_GATE).sort(),
  wieldReqs: list(e.WIELD_REQS).sort(),
  smithReqs: list(e.SMITH_REQS).sort(),
}

// THE VERBS. `INPUT_SCHEMAS` is not exported, so it is read out of the source
// -- which is worth a word, because reading a table out of source text is
// exactly the kind of hand copy this project refuses elsewhere. The difference
// is that this one is not a COPY: it is parsed from the file at the moment it
// is asked, so it cannot drift. If the engine ever exports the table, this
// should be deleted the same day.
import { readFileSync } from 'fs'
const src = readFileSync(new URL('../../interval-bridge/engine.js', import.meta.url), 'utf8')
const at = src.indexOf('const INPUT_SCHEMAS = {')
let depth = 0, end = src.indexOf('{', at)
for (let i = end; i < src.length; i++) {
  if (src[i] === '{') depth++
  else if (src[i] === '}') { depth--; if (!depth) { end = i; break } }
}
out.verbs = [...src.slice(src.indexOf('{', at), end + 1)
  .matchAll(/^\s{2}([a-z_0-9]+)\s*:/gm)].map(m => m[1]).sort()

process.stdout.write(JSON.stringify(out, null, 1))
