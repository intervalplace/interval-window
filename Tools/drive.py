#!/usr/bin/env python3
"""Fetch a file out of a SHARED Google Drive folder, without an API key.

Quaternius's Ultimate Animated Animals is CC0 and lives only on Drive, and
three routes to it failed before this one: it is not on his itch.io (only the
farm animals are), poly.pizza gates its bundle download behind reCAPTCHA, and
the normal Drive folder page is rendered by JavaScript and carries no file ids
in the HTML at all.

`embeddedfolderview` is the way in. It is the plain-HTML view Drive serves for
embedding a folder in a page, it needs no key and no login for a folder that is
shared, and every entry in it carries its id:

    https://drive.google.com/embeddedfolderview?id=<folder>#list

and then the file itself is

    https://drive.google.com/uc?export=download&id=<file>

  drive.py list <folder-id>
  drive.py get  <file-id> <dest>
"""
import re
import sys
import urllib.request

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126 Safari/537.36')


def open_url(url):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={'User-Agent': UA}), timeout=300)


def listing(folder):
    page = open_url('https://drive.google.com/embeddedfolderview?id='
                    + folder + '#list').read().decode('utf8', 'replace')
    return re.findall(r'id="entry-([-\w]+)".*?flip-entry-title">([^<]+)<', page, re.S)


def get(file_id, dest):
    url = 'https://drive.google.com/uc?export=download&id=' + file_id
    with open_url(url) as src:
        body = src.read()
    # A BIG FILE GETS AN INTERSTITIAL, not the bytes: Drive answers with an
    # HTML page carrying a confirm token. Anything under about a hundred
    # megabytes comes straight through, but a pack that grows past it would
    # fail silently as a 3 KB "file", so it is checked rather than assumed.
    if body[:15].lower().startswith(b'<!doctype html') or body[:6] == b'<html>':
        # QUOTA IS THE COMMON ANSWER, not the interstitial. A folder that is
        # shared and popular serves its LISTING for ever and refuses its
        # CONTENTS -- "Google Drive - Quota exceeded" -- and the refusal is a
        # 200 with an HTML body, so anything that does not look at the bytes
        # writes a two-kilobyte web page where a mesh should be.
        if b'Quota exceeded' in body:
            raise SystemExit('drive says quota exceeded for this file; '
                             'the listing still works, the download does not')
        token = re.search(rb'confirm=([\w-]+)', body)
        if not token:
            raise SystemExit('drive answered with a page and no confirm token')
        with open_url(url + '&confirm=' + token.group(1).decode()) as src:
            body = src.read()
    open(dest, 'wb').write(body)
    return len(body)


if __name__ == '__main__':
    if sys.argv[1] == 'list':
        for fid, name in listing(sys.argv[2]):
            print(fid, name)
    else:
        print(get(sys.argv[2], sys.argv[3]), 'bytes ->', sys.argv[3])
