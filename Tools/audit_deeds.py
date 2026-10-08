#!/usr/bin/env python3
"""DOES THE WINDOW BUILD EACH DEED THE WAY THE WORLD READS IT?

THE MEASURE THAT WOULD HAVE CAUGHT `unwield`. That verb sat in the pack's menu
for the whole life of this window and had never once taken a helmet off
anybody: its line filed `slot`, a number, into a field the world types as a
name. Every coverage report counted it reachable, because the line was there
to see and nothing checked what the line actually sent.

So this reads both sides and subtracts them:

  the WORLD's side   `INPUT_SCHEMAS` in engine.js, which names every field a
                     deed must carry -- and every one of them is required,
                     there are no optional fields (see validateInputShape).
  the WINDOW's side  every `Deed(TEXT("verb"), {ints}, {strings})` call in
                     AIntervalHand, which is the one place a deed is built.

A verb the window never builds is not a fault: most verbs reach the world
through the generic path in `ActOnWith`, which fills the fields from the
target. This only reports the verbs the hand builds BY NAME, where the field
list is written out and can therefore be wrong.

AND IT DOES NOT CATCH WHAT CAUGHT `unwield`, WHICH IS WORTH SAYING. That
verb's builder was correct -- it files `{ gear }`, exactly what the world
reads -- and had no caller at all, so the menu reached it through the generic
path, which fills a pack row's `slot` and cannot know a slot's NAME. Nothing
static sees that: the function this would have read is never run.

A check for "builders nothing calls" was written and thrown away, because it
named twenty-seven of them and twenty-seven of them were fine -- they are all
reached by the generic path. A report that is mostly false is a report nobody
reads, which is worse than no report.

What DOES catch it is playing: the bridge now checks every outgoing deed
against the world's own `validateInputShape` and names the fault on the
refusal channel, so a malformed deed says "missing field gear on unwield" in
the feed the moment it is clicked. See `wrongShape` in unreal-bridge.mjs.

  audit_deeds.py
"""
import json
import os
import re
import subprocess
import sys

SP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SP)
HAND = os.path.join(ROOT, 'Plugins', 'IntervalBridge', 'Source', 'IntervalBridge',
                    'Private', 'IntervalHand.cpp')
BRIDGE = os.path.join(os.path.dirname(ROOT), 'interval-bridge')


def world_schema():
    """Every field each verb's schema names, read out of engine.js.

    Parsed rather than imported: `INPUT_SCHEMAS` is not exported, and the
    bridge reads it the same way for the same reason -- see `verbTargets`.
    """
    src = open(os.path.join(BRIDGE, 'engine.js')).read()
    head = src.index('const INPUT_SCHEMAS = {')
    out = {}
    for m in re.finditer(r'(?:\n {2}|,\s*)([A-Za-z_][A-Za-z0-9_]*):\s*\{', src[head:]):
        start = head + m.end() - 1
        depth = 0
        end = start
        for i in range(start, len(src)):
            if src[i] == '{':
                depth += 1
            elif src[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        body = src[head + m.end():end]
        if re.search(r'\n(const|function|module\.exports)\b', src[head:head + m.start()]):
            break
        names = re.findall(r'(?:^\s*|[,{]\s*)([a-z][A-Za-z0-9_]*)\s*:', body)
        out[m.group(1)] = sorted(set(names))
    return out


def window_deeds():
    """{verb: [fields]} for every deed AIntervalHand builds by name."""
    src = open(HAND).read()
    out = {}
    # Deed(TEXT("verb"), { {TEXT("a"), ...}, ... }, { {TEXT("b"), ...}, ... })
    for m in re.finditer(r'Deed\(TEXT\("([a-z_]+)"\)', src):
        verb = m.group(1)
        # Balanced parens from the opening one, so a nested call does not end
        # the argument list early.
        i = src.index('(', m.start())
        depth = 0
        end = i
        for j in range(i, len(src)):
            if src[j] == '(':
                depth += 1
            elif src[j] == ')':
                depth -= 1
                if depth == 0:
                    end = j
                    break
        body = src[i:end]
        # The verb's own TEXT("...") is the first; every later one is a field.
        names = re.findall(r'TEXT\("([a-zA-Z_][a-zA-Z0-9_]*)"\)', body)[1:]
        out.setdefault(verb, set()).update(names)
    return {k: sorted(v) for k, v in out.items()}


def main():
    world = world_schema()
    window = window_deeds()
    print('%d verbs the world types, %d the hand builds by name'
          % (len(world), len(window)))
    print()
    bad = []
    for verb in sorted(window):
        want = world.get(verb)
        if want is None:
            bad.append((verb, 'the world has no schema for this verb', ''))
            continue
        got = window[verb]
        missing = [f for f in want if f not in got]
        extra = [f for f in got if f not in want]
        if missing or extra:
            bad.append((verb,
                        ('missing ' + ' '.join(missing)) if missing else '',
                        ('sends ' + ' '.join(extra) + ', which the schema does not name')
                        if extra else ''))
    if not bad:
        print('every deed the hand builds carries exactly the fields the world reads')
        return
    print('DEEDS THE WORLD WILL NOT READ:')
    for verb, a, b in bad:
        print('  %-16s %s' % (verb, '; '.join(x for x in (a, b) if x)))
    print()
    print('A deed missing a field is refused at the shape check, where a')
    print('refusal never becomes an event -- so the menu line is drawn, the')
    print('click does nothing, and every coverage report counts it reachable.')


if __name__ == '__main__':
    main()
