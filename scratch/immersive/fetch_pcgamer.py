#!/usr/bin/env python3
"""Cache PC Gamer's "History of the best immersive sims", both pages.

    python scratch/immersive/fetch_pcgamer.py

WebFetch 403s on this host, so the pages are fetched with a browser
User-Agent the way scratch/fps/denofgeek-30-best-fps.html was.

Each page arrives as about 2 MB of markup, nearly all of it scripts, inline
SVG and image srcsets. That is not worth committing, so the scripts, styles,
SVG and comments are stripped and the file is cut down to the article region
before it is written — everything scratch/immersive/parse_pcgamer.py reads
(the dated <h2> picks, the two page-2 section anchors and the bold paragraph
titles under them) survives untouched, and the cached file lands around a
tenth of the size. Re-running parse_pcgamer.py after a re-fetch must produce
a byte-identical pcgamer.json; if it does not, the article changed and the
generator's asserts are the place that will say so.

Pages 3 and 4 exist and serve page 1 again, so there are only two.
"""
import pathlib
import re
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
URL = "https://www.pcgamer.com/history-of-the-best-immersive-sims/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")

PAGES = [(URL, "pcgamer-history-immersive-sims.html"),
         (URL + "2/", "pcgamer-history-immersive-sims-2.html")]


def trim(html):
    """Drop everything the parse cannot use, keep the article markup."""
    for pat in (r"<script\b.*?</script>", r"<style\b.*?</style>",
                r"<svg\b.*?</svg>", r"<noscript\b.*?</noscript>",
                r"<!--.*?-->", r"<source\b[^>]*>", r"<picture\b.*?</picture>"):
        html = re.sub(pat, "", html, flags=re.S | re.I)
    # keep from the headline to the end of the author block
    i = html.find("<h1")
    if i > 0:
        html = html[i:]
    html = re.sub(r"[ \t]+\n", "\n", html)
    return re.sub(r"\n{3,}", "\n\n", html)


def main():
    for url, name in PAGES:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA, "Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read().decode("utf-8", "replace")
        out = trim(raw)
        assert "immersive sim" in out.lower(), "%s came back wrong" % url
        (HERE / name).write_text(out, encoding="utf-8", newline="\n")
        print("%-42s %7d bytes fetched, %7d kept"
              % (name, len(raw), len(out)))


if __name__ == "__main__":
    main()
