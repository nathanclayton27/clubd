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

git add -- index.html build.json <the source files you changed>
git commit
git push origin main
```

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
- **It does not publish anything from `scratch/`.** That directory is
  gitignored and holds working material, credentials-adjacent tooling and
  security notes. Keep it that way.
