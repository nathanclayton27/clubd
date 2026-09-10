# Deploying clubd

The site is static. `src/template.html` is the source, `index.html` is
generated, and GitHub Pages serves `index.html` from `main` at
**clubd.watch**.

There is exactly one origin. That sentence is the whole point of this file —
see [The step that was removed](#the-step-that-was-removed).

## The procedure

```sh
python src/build.py                    # src/template.html + properties/ -> index.html
python scratch/jscheck.py index.html   # the generated <script> block parses
python tools/qa_lint.py                # content rules: notes, counts, blurbs

git add -- index.html build.json l <the source files you changed>
git commit
git push origin main
```

### `l/` ships with `index.html` too

The build writes one share page per public list into `l/` — the file a
crawler reads instead of `index.html`, so a pasted link previews as the list
rather than as the site (see *Share pages* in `HOW-IT-WORKS.md`). It owns the
directory: a new list gets a page, a renamed or removed list loses its old one.
Stage the whole directory, not the files you happen to notice; the CI check
fails on a page that is stale or untracked.

### `build.json` ships with `index.html`, always

`src/build.py` writes both, and they are a matched pair. The page carries its
own build id and polls `build.json`; when the two differ it assumes a new
version has been deployed and reloads itself once.

So committing `index.html` **without** `build.json` gives every visitor a
spurious reload on arrival, and it keeps happening until the pair is back in
step. It is not an infinite loop — a `sessionStorage` guard limits it to once
per session — which is exactly why it can go unnoticed. It shipped that way on
2026-08-27 and was found by reading `git status`, not by anything failing.

Check before you push:

```sh
grep -o "BUILD = '[a-f0-9]*'" index.html    # must equal
cat build.json                              # ...this
```

Pages redeploys in about thirty seconds. Verify against the live site rather
than the local file — a green build is not a green deploy:

```sh
curl -s -o /dev/null -w '%{http_code}\n' https://clubd.watch/
```

### Never `git add -A`

Stage the files you changed, by name. A blanket add once swept a security
document describing two unpatched criticals onto the live site, where it sat
for about twenty minutes. `scratch/` is gitignored precisely so that working
material cannot reach the public site, and `git add -A` is the one command that
routinely defeats a `.gitignore` the moment something is accidentally tracked.

Check what you are about to publish before you push:

```sh
git show --stat
```

### Never end with a blanket restore

`git checkout -- .` restores **every tracked file** to HEAD. Agents write into
this same working tree and several are usually live at once, so a blanket
restore silently destroys their uncommitted edits to existing files. It wiped
the same list repair twice in one evening before anyone worked out what was
doing it. Restore by name, or not at all.

The same applies to `git reset --hard`, `git stash -u` and `git clean`.

## The step that was removed

Until 27 August 2026 every deploy ended with a second push:

```sh
git push -f legacy legacy-sync:main    # DO NOT RUN THIS. It is retired.
```

That mirrored the entire site to the old GroupWatch origin, which meant
`nathanclayton27.github.io/GroupWatch/` returned HTTP 200 and the **current**
build — a second live front door onto the same Supabase project. Anyone
following an old link was using the real app at the wrong address, and two
origins for one app only have to disagree once about an auth redirect, a cookie
domain or an RLS assumption.

**That origin now serves a redirect and nothing else** (CLU-68). It has no
build, no Supabase key and no reason to change again.

**Running that push again would silently restore the duplicate site.** Nothing
would surface it: the deploy would succeed, the real site would look correct,
and the old address would quietly start serving a live copy of clubd again.
There is no alert for this, which is why it is written down here instead.

The `legacy` remote still exists so the old repository's history is reachable.
It is not part of deploying.

## Things the deploy does not do

- **It does not run migrations.** SQL is written here and run by hand in the
  Supabase SQL editor, and a migration is audited by someone other than its
  author before it is queued. Code shipping ahead of its migration is the most
  common way a feature half-works in production.
- **It does not touch `CNAME`.** It contains `clubd.watch` and is what binds
  the custom domain. Deleting it takes the site off its own domain.
- **It publishes every tracked file, including tracked files under `scratch/`.**
  That sentence used to read "it does not publish anything from `scratch/`", and
  it was false. `.gitignore` stops a file becoming tracked; it does nothing once
  one already is, and Pages serves what is tracked. Two QA harnesses had slipped
  in, so `clubd.watch/scratch/qa2/privacy_check.py` answered **200** with the
  whole privacy model written out as assertions — published, for anyone who
  guessed the path.

  Both are untracked now, and the guard that keeps it that way is a command, not
  a sentence:

  ```sh
  python tools/notracked.py
  ```

  It fails if anything is tracked under `scratch/qa2/`, `scratch/security/`,
  `scratch/linear/` or an `audit*/`, if any tracked `scratch/` file is a `.md`,
  `.sql`, `.txt` or `.env`, or if any of them contains a credential marker. Run
  it before you push.

  What *is* tracked under `scratch/` on purpose: the per-property harvest scripts
  and their cached sources (`scratch/<property>/collect.py`, `*.wiki`, `*.json`).
  Those are build inputs — they are how a clone re-runs
  `tools/make_<property>.py` and gets the same list back — and they hold nothing
  but public source text. The gated list is not among them: its slug and title in
  `properties/index.json` are placeholders, so nothing in the repo names it.
