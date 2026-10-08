// COULD SOMEBODY PLAY THIS WINDOW AND DO EVERYTHING THE WORLD ALLOWS?
//
// That is the standing test this project is measured against, and until now it
// has only ever been answered by remembering. This answers it by counting.
//
// Three sources, none of them a list anybody maintains by hand:
//   - the ENGINE's own verbs, read out of engine.js
//   - what the BRIDGE says each node and each item affords, which is what the
//     right-click menu is built from, asked of the running bridge
//   - the handful the HAND adds itself, read out of IntervalHand.cpp
//
// A verb is REACHABLE if a person with a mouse can get to it. Filing it from
// code does not count and never has: the window could file most of these long
// before any of them had a button, which is exactly the gap that made a window
// look finished and be unplayable.
//
//   node coverage.mjs            -- the report
//   node coverage.mjs --json     -- the same, machine readable
//
// Run it from the bridge's directory; see Tools/coverage.sh.
import fs from 'fs'
import { WebSocket } from 'ws'
import { fileURLToPath } from 'node:url'
import { execFileSync } from 'node:child_process'

// THE ENGINE THIS PROJECT ACTUALLY RUNS, not a copy in Downloads.
//
// This pointed at `~/Downloads/interval-main/engine.js`, a file unpacked on 9
// September and never touched since. Every run of this report since then has
// answered the standing question -- can somebody play the whole world through
// this window -- about a DIFFERENT world: it still listed `alch` and `special`
// as verbs months after they were renamed to `transmute` and `gambit`, so a
// report saying nothing is out of reach was saying it about verbs the engine
// no longer has, and could not have seen a new verb at all.
//
// `audit_motion.py` had the same line and the same fault. Both read the bridge
// now, which is the only copy a node ever runs.
// (`fileURLToPath`, not `.pathname`: this project lives under "Unreal
// Projects" and a URL keeps that space as %20, which no filesystem call will
// open.)
const ENGINE = fileURLToPath(new URL('./engine.js', import.meta.url))
// The bridge decides what a PLACE allows; see `bridgeVerbs`.
const BRIDGE = '/Users/matsjulner/Documents/Unreal Projects/interval-bridge/unreal-bridge.mjs'
const HAND = '/Users/matsjulner/Documents/Unreal Projects/interval/Plugins/' +
             'IntervalBridge/Source/IntervalBridge/Private/IntervalHand.cpp'
const HUD = '/Users/matsjulner/Documents/Unreal Projects/interval/Plugins/' +
            'IntervalBridge/Source/IntervalBridge/Private/IntervalHud.cpp'

// The world does these TO a citizen -- a body rots, an hour wakes you, the
// world moves a beast. Nobody wants a button for them and their absence is
// not a gap.
const NOT_OURS = new Set(['move', 'rot', 'spawn', 'stop', 'taking', 'turn',
                          'waking', 'withering'])

// AND THE ONES THE WORLD ITSELF WILL NOT TAKE FROM ANYBODY.
//
// `read_chart` and `recall` are `case 'x': return false` in this founding --
// not gated, not conditional, refused outright -- so no window can reach them
// and a window that drew a line for them would be lying. `attend` is not in
// validInput at all: it is the vigil in Nought, and the window reaches it
// through the crossing rather than through a menu.
//
// `archive` and `restore` ask for a merkle path over the world's own ledger,
// which is a thing a node answers and not a thing a player points at.
//
// Counting these as gaps made the report say the window was six verbs short
// when it was one. They are listed separately so the one real gap is visible.
const NOT_POSSIBLE = new Map([
  ['read_chart', 'the world refuses it in this founding'],
  ['recall',     'the world refuses it in this founding'],
  ['attend',     'the vigil in Nought; reached by crossing, not by a menu'],
  ['archive',    'wants a merkle path, which is a node\'s answer'],
  ['restore',    'wants a merkle path, which is a node\'s answer'],
])

const engineVerbs = () => {
  const src = fs.readFileSync(ENGINE, 'utf8')
  return new Set([...src.matchAll(/inp\.type === '([a-z_]+)'/g)].map(m => m[1]))
}

// The tables in IntervalHand.cpp whose entries ARE menu rows. See the note
// where this is used for why they are named rather than recognised.
const ROW_TABLES = ['Reads', 'Underfoot', 'Ground']
const rowTables = (src) => {
  const out = []
  for (const name of ROW_TABLES) {
    const at = src.indexOf(`TMap<FString, FString> ${name} = {`)
    if (at < 0) continue
    const end = src.indexOf('};', at)
    for (const m of src.slice(at, end).matchAll(/TEXT\("([a-z_]+)"\)\s*,/g)) {
      out.push(m[1])
    }
  }
  return out
}

const handVerbs = (engine) => {
  // FILTERED AGAINST THE ENGINE, because the same `Add(TEXT("..."))` shape is
  // used for the FIELD names a deed carries -- `dx`, `dy`, `steps`, `style` --
  // and counting those as verbs the player can reach would flatter the answer.
  const src = fs.readFileSync(HAND, 'utf8')
  // `AddUnique` AS WELL AS `Add`. A verb that is not something an ITEM
  // affords -- `deposit`, which is something the PLACE affords -- is pushed
  // into the list before it is sorted, and that is written `AddUnique`. This
  // pattern missed it entirely and reported `deposit` out of reach on a day
  // it had been used through the window a dozen times, which is exactly the
  // kind of wrong answer this report exists to prevent somebody else making.
  const all = [
    ...[...src.matchAll(/Add(?:Unique)?\(TEXT\("([a-z_]+)"\)/g)].map((m) => m[1]),
    // AND THE VERBS THAT ARE DRAWN FROM A TABLE RATHER THAN NAMED IN A CALL.
    //
    // The citizen's menu stopped listing every social verb and started
    // drawing only the ones the bridge says are open, which moved the verbs
    // out of eight `Add(TEXT("..."))` lines and into a table of what each one
    // READS as. Counting only the calls, this reported eight verbs lost on a
    // day none of them was -- the same false alarm as `AddUnique`, one step
    // along.
    // A ROW, not merely a WORDING.
    //
    // The window keeps tables that look alike and mean different things. One
    // says how a verb READS on a row it is already drawing (`deposit_all` ->
    // "put everything away"); the others ARE the rows, listing what a citizen
    // or a tile offers. Only the second kind is reachability.
    //
    // Told apart BY NAME, and the names are here because every attempt to
    // tell them apart by shape has been wrong: matching every such table
    // credited the window with `set_look`, and matching only the ones whose
    // labels carry a `{}` lost `kindle`, `raise_market` and `survey` the day
    // they were added. A new table of rows must be named below, and if it is
    // not, this report will say a verb is out of reach that is in it -- which
    // is the failure that gets noticed rather than the one that flatters.
    ...rowTables(src),
  ]
  return new Set(all.filter((v) => engine.has(v)))
}

// ---- THE VERBS THE INTERFACE REACHES WITHOUT A MENU ----
//
// Not everything a player can do goes through a right click. The spellbook's
// rows call the hand directly, and this report was counting `cast` as out of
// reach for as long as it has existed -- which is the same failure it was
// built to catch, one level up.
//
// Derived, not listed: find every `Hand->Something(` in the HUD, then look up
// what `AIntervalHand::Something` actually files. If somebody wires a new
// button tomorrow it is counted tomorrow.
const hudVerbs = (engine) => {
  const hud = fs.readFileSync(HUD, 'utf8')
  const hand = fs.readFileSync(HAND, 'utf8')

  // The menu plumbing is counted elsewhere and its bodies name every verb in
  // the world; scanning them here would credit the panels with everything the
  // right-click menu can do and flatter the answer badly. A first pass did
  // exactly that and reported fifty-six.
  const MENU = new Set(['ActOnWith', 'ActOn', 'OptionsFor', 'VerbUnderCursor',
                        'WalkRoute', 'GetRouteGoal', 'TargetsUnderCursor'])
  const called = [...new Set(
    [...hud.matchAll(/Hand->([A-Z][A-Za-z0-9_]*)\s*\(/g)].map((m) => m[1]))]
    .filter((fn) => !MENU.has(fn))

  const out = new Set()
  for (const fn of called) {
    const at = hand.indexOf(`AIntervalHand::${fn}(`)
    if (at < 0) continue
    // THE FUNCTION'S OWN BODY, by counting braces. A fixed slice of characters
    // runs into whatever is written underneath, which is how `smith` and
    // `smelt` ended up credited to the spellbook.
    let i = hand.indexOf('{', at)
    if (i < 0) continue
    let depth = 0
    let end = i
    for (; i < hand.length; i++) {
      if (hand[i] === '{') depth++
      else if (hand[i] === '}') { depth--; if (depth === 0) { end = i; break } }
    }
    const body = hand.slice(at, end)
    // EVERY WAY THE HAND FILES A DEED, not three of the six. `Plain` is
    // `Deed` with no fields and is how the verbs that name nothing at all go
    // out -- `cancel_trade`, `deposit_all`, `stop` -- so a panel button
    // wired to one of those was reported as reaching nothing.
    for (const m of body.matchAll(
      /(?:Deed|Plain|SendIntent|SendIntentBool|SendIntentList)\s*\(\s*TEXT\("([a-z_]+)"\)/g)) {
      if (engine.has(m[1])) out.add(m[1])
    }
  }
  return out
}

// AND THE BRIDGE ON THE OTHER END MUST NOT BE OLDER THAN THE RULES.
//
// `itemAffords` is computed at boot from the engine the bridge loaded, so a
// bridge left running from yesterday answers with yesterday's vocabulary and
// there is nothing in the reply that says so. That is exactly what happened:
// this report said `transmute` was out of reach while the bridge source had
// afforded it for hours, because the process being asked had started before
// the rename and was still offering `alch`.
//
// A report that can be wrong about the thing it exists to measure is worse
// than no report. So the age of the process is checked against the age of
// engine.js, and an older one is refused rather than believed.
const bridgeIsStale = () => {
  const pid = (() => {
    try {
      return execFileSync('/usr/sbin/lsof', ['-tnP', '-iTCP:7777', '-sTCP:LISTEN'],
        { encoding: 'utf8' }).trim().split('\n')[0]
    } catch { return '' }
  })()
  if (!pid) return null
  try {
    // ELAPSED TIME, NOT A DATE. `ps -o lstart` prints in the machine's own
    // locale -- on this one "lør. 26 sep. 10.35.11 2026" -- which `new Date`
    // reads as NaN, so the first cut of this check silently never fired and
    // the stale bridge went on being believed. `etime` is [[dd-]hh:]mm:ss
    // everywhere.
    const etime = execFileSync('/bin/ps', ['-o', 'etime=', '-p', pid],
      { encoding: 'utf8' }).trim()
    const m = etime.match(/^(?:(\d+)-)?(?:(\d+):)?(\d+):(\d+)$/)
    if (!m) return null
    const secs = (+(m[1] || 0)) * 86400 + (+(m[2] || 0)) * 3600
      + (+m[3]) * 60 + (+m[4])
    const up = Date.now() - secs * 1000
    const rules = fs.statSync(ENGINE).mtimeMs
    if (up < rules) {
      const hours = ((rules - up) / 3600000).toFixed(1)
      return `the bridge on 7777 (pid ${pid}) has been up ${etime}, which is`
        + ` ${hours} hours longer than the current engine.js has existed. It is`
        + ` answering with the vocabulary it booted with. Restart it, or this`
        + ` report is about a world nobody is running.`
    }
  } catch { /* if it cannot be asked, do not block the report */ }
  return null
}

const fromBridge = () => new Promise((ok, no) => {
  const w = new WebSocket('ws://127.0.0.1:7777')
  const t = setTimeout(() => { w.close(); no(new Error('the bridge did not say hello')) }, 15000)
  w.on('message', (d) => {
    const m = JSON.parse(d)
    if (m.k !== 'hello') return
    clearTimeout(t)
    const node = new Set(), item = new Set()
    for (const k of Object.keys(m.affords ?? {})) for (const v of m.affords[k]) node.add(v)
    for (const k of Object.keys(m.itemAffords ?? {})) for (const v of m.itemAffords[k]) item.add(v)
    w.close(); ok({ node, item, fields: m.verbFields ?? {}, takes: m.verbTakes ?? {} })
  })
  w.on('error', no)
})

// ---- AND WHETHER THE WINDOW COULD ACTUALLY FILL THE DEED IN ----
//
// Being afforded is not the same as being reachable. `set_look` is afforded by
// the looking-glass and wants a number nothing can type; `consign` is afforded
// by a store and wants a list of slots; `price_market` wants a sum. The window
// declines to draw a row it cannot fill -- that is `CanFile` in
// IntervalBridgeSubsystem.h -- so counting the affordance alone reports verbs
// as reachable that a player will never see.
//
// This mirrors that rule, deliberately, and it mirrors it PER ROW: a slot is
// something a pack cell knows and a tree does not. Keeping the two in step by
// hand is the usual trap, so the shape below is written to read like the C++
// it is echoing, and if they drift the honest failure is this report saying a
// verb is out of reach that is in it -- which somebody will notice.
// The verbs whose thing the window offers by name itself, on a second page.
// `smelt` is `smith` asked at a furnace and reads the same recipe table.
//
// `rifle` and `grave` joined them when the window learned to read a hoard's
// shelf and the people standing at a stone: both name a second thing, both
// now offer it by name, and both were counted out of reach for as long as
// they did not.
// `consign` is the odd one: what its page offers is a LIST of slots, and the
// window builds the list itself from the answer rather than putting a word in
// a field. It is counted here because a player can reach it, which is the only
// question this report asks.
const CHOICE = new Set(['buy', 'smith', 'smelt', 'fletch', 'set_look',
                        'rifle', 'grave', 'consign'])
const canFill = (verb, fields, takes, kind) => {
  const named = fields[verb]
  if (!named) return true               // no schema known: the world decides
  const points = (takes[verb] ?? [])[0]
  return named.every((f) => {
    if (f === points) return true
    if (['nodeId', 'mobId', 'targetId', 'style'].includes(f)) return true
    if ((f === 'slot' || f === 'gear') && kind === 'pack') return true
    if ((f === 'groundId' || f === 'confirm') && kind === 'drop') return true
    if ((f === 'item' || f === 'qty') && kind === 'vault') return true
    // The words a menu line carries because the window offered it by name:
    // an item, a recipe, a make, a face. `look` joined them when the window
    // learned to draw a chosen face instead of only an inherited one.
    if (['item', 'recipe', 'make', 'look', 'target', 'slots'].includes(f)
        && CHOICE.has(verb)) return true
    // A FIGURE THE WINDOW ASKS FOR IN A BOX. `ask`, `n` and `pay` are numbers
    // no menu can offer sensibly -- a stall's price is any sum at all -- so
    // the row opens the same entry the trade plate uses. See `Figures` in
    // ActOnWith, and CanFile, which this mirrors.
    if (['ask', 'n', 'pay'].includes(f)) return true
    return false
  })
}

// ---- AND WHAT THE BRIDGE DECIDES A PLACE ALLOWS ----
//
// `verbsBeside` and `underfoot` name verbs the affordance tables do not: a
// plot does not afford `plant` and seeds do not either, it is both and neither
// table says so. The window draws whatever comes back in those lists, so the
// list in the bridge IS the reachability, and reading it here is reading the
// same source the window reads.
const bridgeVerbs = (engine) => {
  const src = fs.readFileSync(BRIDGE, 'utf8')
  const out = new Set()
  for (const fn of ['function verbsBeside', 'function underfoot']) {
    const at = src.indexOf(fn)
    if (at < 0) continue
    const end = src.indexOf('\n}', at)
    for (const m of src.slice(at, end).matchAll(/out\.(?:add|push)\('([a-z_]+)'\)/g)) {
      if (engine.has(m[1])) out.add(m[1])
    }
  }
  return out
}

const main = async () => {
  const stale = bridgeIsStale()
  if (stale) { console.log('\n  REFUSING TO REPORT: ' + stale + '\n'); process.exit(2) }
  const engine = engineVerbs()
  const hand = handVerbs(engine)
  const place = bridgeVerbs(engine)
  const { node, item, fields, takes } = await fromBridge()
  const hud = hudVerbs(engine)
  // A NODE'S VERBS ARE CHECKED AS A NODE'S, a pack's as a pack's. The hand's
  // own lines and the panels' buttons are written deliberately and supply
  // whatever they name, so they are taken at their word.
  const nodeOk = new Set([...node].filter((v) => canFill(v, fields, takes, 'node')))
  // A VERB THE GROUND ALLOWS THAT WANTS A SLOT IS A PACK VERB.
  //
  // `cook`, `brew`, `grind`, `bury`, `stoke`, `deposit` and the rest are
  // afforded by a node and carried out on a thing in the pack, so the window
  // draws them on the pack's rows whenever the place that allows them is in
  // reach. Counting them as node verbs said they were unreachable; counting
  // them nowhere said the same. They are reachable, from the cells.
  const itemOk = new Set([...item].filter((v) => canFill(v, fields, takes, 'pack')))
  for (const v of node) {
    if ((fields[v] ?? []).includes('slot') && canFill(v, fields, takes, 'pack')) {
      itemOk.add(v)
    }
  }
  const reach = new Set([...nodeOk, ...itemOk, ...hand, ...hud, ...place]
    .filter((v) => engine.has(v)))
  const gap = [...engine].filter((v) => !reach.has(v) && !NOT_OURS.has(v)
                                    && !NOT_POSSIBLE.has(v)).sort()
  const shut = [...engine].filter((v) => NOT_POSSIBLE.has(v)).sort()
  const theirs = [...engine].filter((v) => NOT_OURS.has(v)).sort()

  if (process.argv.includes('--json')) {
    console.log(JSON.stringify({ engine: engine.size, reachable: reach.size,
                                 gap, worlds: theirs }, null, 1))
    return
  }
  console.log('')
  console.log('  the world allows          %d verbs', engine.size)
  console.log('  a player can reach        %d', reach.size)
  console.log('  the world does to you     %d  (no button wanted)', theirs.length)
  console.log('  no window can reach       %d  (see below)', shut.length)
  console.log('  STILL OUT OF REACH        %d', gap.length)
  console.log('')
  console.log('  reachable by right-clicking a thing in the world (%d):', nodeOk.size)
  console.log('   ', [...nodeOk].sort().join(' '))
  const shy = [...node].filter((v) => !nodeOk.has(v) && !itemOk.has(v)).sort()
  if (shy.length) {
    console.log('    (afforded but unfillable, so not drawn: %s)', shy.join(' '))
  }
  console.log('')
  console.log('  reachable by right-clicking a thing in the pack (%d):', itemOk.size)
  console.log('   ', [...itemOk].sort().join(' '))
  console.log('')
  console.log('  the hand offers itself (%d):', hand.size)
  console.log('   ', [...hand].sort().join(' '))
  console.log('')
  console.log('  reachable from a panel, without a menu (%d):', hud.size)
  console.log('   ', [...hud].sort().join(' '))
  console.log('')
  if (shut.length) {
    console.log('  NOT REACHABLE BY ANY WINDOW:')
    for (const v of shut) console.log('    ' + v.padEnd(12) + ' ' + NOT_POSSIBLE.get(v))
    console.log('')
  }
  console.log('  OUT OF REACH -- nothing a mouse can do gets here:')
  for (let i = 0; i < gap.length; i += 8) {
    console.log('   ', gap.slice(i, i + 8).join(' '))
  }
  console.log('')
}

main().catch((e) => { console.error(e.message); process.exit(1) })
