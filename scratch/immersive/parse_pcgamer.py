#!/usr/bin/env python3
"""Parse PC Gamer's "History of the best immersive sims" into three tiers.

    python scratch/immersive/parse_pcgamer.py

Reads the cached pages (fetched with a browser User-Agent; WebFetch 403s on
this host) and writes scratch/immersive/pcgamer.json:

  * "canon"   — page 1's dated picks, each an <h2> of the form
                "1992: Ultima Underworld". Ten of them. This is the published
                canon tools/make_immersive.py counts as a source that a game
                IS an immersive sim.
  * "indies"  — page 2, "Inspired indies": "indie devs bravely taking on the
                formidable challenge of immersive sims".
  * "outside" — page 2, "Inspired sims", introduced as "Games outside the
                immersive sim genre make use of some of its traits". This is
                the only NEGATIVE evidence in the whole build: a game the
                feature files here is one the feature says is not one, and
                the generator refuses to ship it however loudly Wikipedia's
                category disagrees. It is what keeps Alien: Isolation and the
                Hitman games off the list on a citation rather than on taste.

Both page-2 sections title their entries as a whole paragraph of bold text —
<p><strong>Neon Struct</strong></p> — rather than as headings, so they are
read that way. The article's own spellings are kept exactly as published,
typos and all ("Thief 2: The MEtal Age"); matching happens through
gwlib.prop.normt, never by fixing the source.
"""
import html
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
PAGE1 = HERE / "pcgamer-history-immersive-sims.html"
PAGE2 = HERE / "pcgamer-history-immersive-sims-2.html"

DATED = re.compile(r"^(19|20)(\d{2}):\s*(.*\S)\s*$")
BOLD_P = re.compile(r"<p[^>]*>\s*<strong>(.*?)</strong>\s*</p>", re.S)


def text(raw):
    return html.unescape(re.sub(r"<[^>]+>", "", raw)).replace("\xa0", " ").strip()


def main():
    p1 = PAGE1.read_text(encoding="utf-8", errors="replace")
    canon = []
    for raw in re.findall(r"<h2[^>]*>(.*?)</h2>", p1, re.S):
        m = DATED.match(text(raw))
        if m:
            canon.append({"year": int(m.group(1) + m.group(2)),
                          "title": m.group(3)})
    assert len(canon) == 10, "expected 10 dated picks, parsed %d" % len(canon)
    assert len({c["title"] for c in canon}) == 10, "a pick repeats"

    p2 = re.sub(r"<script.*?</script>", " ",
                PAGE2.read_text(encoding="utf-8", errors="replace"),
                flags=re.S)
    bounds = {}
    for key, anchor in (("indies", "inspired-indies"),
                        ("outside", "inspired-sims")):
        m = re.search(r'<h2 id="%s"' % anchor, p2)
        assert m, "page 2 no longer has the %s section" % anchor
        bounds[key] = m.start()
    assert bounds["indies"] < bounds["outside"], "sections swapped order"

    tiers = {}
    for key, start, end in (("indies", bounds["indies"], bounds["outside"]),
                            ("outside", bounds["outside"], len(p2))):
        seen = []
        for raw in BOLD_P.findall(p2[start:end]):
            t = text(raw)
            # the section's own standfirst is bold too; entries are short
            if not t or len(t) > 60 or t.endswith(".") or t in seen:
                continue
            seen.append(t)
        assert seen, "no entries parsed for %s" % key
        tiers[key] = seen

    out = {"source": "PC Gamer, History of the best immersive sims",
           "canon": canon, **tiers}
    (HERE / "pcgamer.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n")

    for c in canon:
        print("canon    %d  %s" % (c["year"], c["title"]))
    for key in ("indies", "outside"):
        for t in tiers[key]:
            print("%-8s      %s" % (key, t))


if __name__ == "__main__":
    main()
