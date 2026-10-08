#!/usr/bin/env python3
"""Find and fetch CC0 models from poly.pizza.

WHY THIS AND NOT THE OTHER THREE ROUTES. Quaternius's wild animals are CC0 and
the pack itself is effectively unreachable: not on his itch.io (only the farm
animals are), and the official link is a Google Drive folder that serves its
LISTING for ever and answers every download with "Quota exceeded". poly.pizza
mirrors the same models one at a time, and while its BUNDLE button is behind a
reCAPTCHA, each model's own page carries a plain CDN link to the .glb.

THE LICENCE IS READ OFF THE PAGE, not assumed from the site. poly.pizza hosts
CC-BY work alongside CC0 and says which on every model; a search filter is not
a licence, which this project has been bitten by once already (an OpenGameArt
pack the site's own CC0 filter returned says CC-BY 4.0 in its own field).

  polypizza.py find <word> [...]         -- what is there, with its licence
  polypizza.py get <slug> <dest.glb>     -- fetch one, refusing anything but CC0
"""
import re
import sys
import time
import urllib.request
import urllib.error

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126 Safari/537.36')


LAST = [0.0]


def page(url):
    """One request at a time, and not too fast.

    poly.pizza answers 429 after about a dozen pages in quick succession, and
    it answers it to the SEARCH as well as to the model, so a sweep of ten
    creatures comes back mostly empty and looks like a site with nothing on
    it. A second and a half between requests is enough; a sweep takes a couple
    of minutes and finishes.
    """
    for attempt in range(4):
        wait = 1.5 - (time.time() - LAST[0])
        if wait > 0:
            time.sleep(wait)
        LAST[0] = time.time()
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers={'User-Agent': UA}),
                timeout=180).read().decode('utf8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 3:
                raise
            time.sleep(6 * (attempt + 1))
    raise SystemExit('poly.pizza kept answering 429')


def find(word):
    html = page('https://poly.pizza/search/' + urllib.parse.quote(word))
    seen, out = set(), []
    for slug in re.findall(r'"/m/([A-Za-z0-9_-]+)"', html):
        if slug in seen:
            continue
        seen.add(slug)
        out.append(slug)
    return out


def about(slug):
    html = page('https://poly.pizza/m/' + slug)
    glb = re.search(r'https://static\.poly\.pizza/[0-9a-f-]+\.glb', html)
    title = re.search(r'<title>([^<]*)</title>', html)
    # The licence line and the author sit in the page's own metadata.
    lic = 'CC0' if re.search(r'\bCC0\b', html) else (
        'CC-BY' if re.search(r'CC-?BY', html) else '?')
    who = 'Quaternius' if 'Quaternius' in html else (
        re.search(r'by ([A-Za-z0-9 _.-]{2,30})', html).group(1)
        if re.search(r'by ([A-Za-z0-9 _.-]{2,30})', html) else '?')
    return {'slug': slug, 'title': (title.group(1).split('|')[0].strip()
                                    if title else slug),
            'licence': lic, 'by': who, 'glb': glb.group(0) if glb else None}


def get(slug, dest):
    it = about(slug)
    if it['licence'] != 'CC0':
        raise SystemExit('%s is %s, not CC0 -- not taking it' % (slug, it['licence']))
    if not it['glb']:
        raise SystemExit('%s has no .glb on its page' % slug)
    body = urllib.request.urlopen(
        urllib.request.Request(it['glb'], headers={'User-Agent': UA}),
        timeout=600).read()
    if body[:4] != b'glTF':
        raise SystemExit('%s did not answer with a glB' % it['glb'])
    open(dest, 'wb').write(body)
    print('%s (%s, %s) -> %s  %d KB' % (it['title'], it['licence'], it['by'],
                                        dest, len(body) // 1024))


if __name__ == '__main__':
    import urllib.parse
    if sys.argv[1] == 'find':
        for word in sys.argv[2:]:
            print('== ' + word)
            for slug in find(word)[:8]:
                it = about(slug)
                print('   %-14s %-28s %-6s %s' % (it['slug'], it['title'][:28],
                                                  it['licence'], it['by'][:18]))
    else:
        get(sys.argv[2], sys.argv[3])
