#!/usr/bin/env python3
"""Fetch a free CC0 pack from itch.io.

itch's own page does this with JavaScript, and the shape of it is not obvious
from outside, so it is written down here rather than rediscovered:

  1. GET the pack page with a cookie jar. itch sets `itchio_token`, which is
     the csrf token for the anonymous session.
  2. POST that token to `<pack>/download_url`. It answers with a SIGNED
     download-page URL -- this is what "Download Now" opens.
  3. GET that page, WITH THE SAME COOKIES. It carries the upload ids and a
     fresh csrf token of its own in a hidden field.
  4. POST that second token to `<pack>/file/<upload id>?source=game_download`.
     NOT to the download page's path, and with NO key parameter -- the key is
     already in the session cookie, and passing it is what makes itch answer
     "invalid key". It returns a storage URL that is good for sixty seconds.

  itch.py <pack-slug> <dest.zip>
"""
import http.cookiejar, json, re, sys, urllib.parse, urllib.request

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126 Safari/537.36')


def main(slug, dest, want=None):
    jar = http.cookiejar.CookieJar()
    web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    web.addheaders = [('User-Agent', UA)]
    base = 'https://quaternius.itch.io/' + slug

    page = web.open(base, timeout=60).read().decode('utf8', 'replace')
    # A REAL DECLARATION, not the three letters appearing anywhere on the page.
    # "CC0" alone matches a "more from this creator" tile advertising some other
    # pack, which would let an all-rights-reserved kit through on a neighbour's
    # licence. What counts is the formal tag, the author's own words, or the
    # dedication's URL.
    says = ('creative commons zero', 'cc0 license', 'cc0 licence',
            'creativecommons.org/publicdomain/zero')
    low = page.lower()
    if not any(w in low for w in says):
        raise SystemExit('%s does not declare CC0 on its page -- not taking it' % slug)
    token = next(c.value for c in jar if c.name == 'itchio_token')

    body = urllib.parse.urlencode({'csrf_token': token}).encode()
    url = json.loads(web.open(base + '/download_url', body, timeout=60).read())['url']

    dl = web.open(url, timeout=60).read().decode('utf8', 'replace')
    csrf = re.search(r'csrf_token" value="([^"]+)"', dl).group(1)
    # Each upload is a button; the free one is the only one listed for a pack
    # whose paid tier the account has not bought.
    uploads = re.findall(r'data-upload_id="(\d+)"', dl)
    if not uploads:
        raise SystemExit('%s: no free download on that page' % slug)
    # The file name is not always in the markup this page uses, so the id is
    # the thing to trust and the name is decoration. Zipping the two together
    # and filtering on the name silently emptied the list when the name was
    # missing, which looked exactly like "there is no free download".
    names = re.findall(r'class="name"[^>]*>([^<]+)<', dl) \
        or re.findall(r'<strong title="([^"]+)"', dl)
    pairs = [(u, names[i] if i < len(names) else '?') for i, u in enumerate(uploads)]
    if want and len(pairs) > 1:
        pairs = [p for p in pairs if want.lower() in p[1].lower()] or pairs
    uid, name = pairs[0]
    print('%s -> %s' % (slug, name))

    body = urllib.parse.urlencode({'csrf_token': csrf}).encode()
    r = web.open(base + '/file/' + uid + '?source=game_download', body, timeout=60)
    store = json.loads(r.read())['url']

    with web.open(store, timeout=900) as src, open(dest, 'wb') as out:
        while True:
            block = src.read(1 << 20)
            if not block:
                break
            out.write(block)
    print('  saved', dest)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
