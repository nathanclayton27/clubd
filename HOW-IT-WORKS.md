# How it works

The single technical document for GroupWatch. It replaces the old
`HANDOFF.md`, `HOW-IT-WORKS.md` and `PLAN.md`, which described the app when it
tracked one hardcoded reading order and had drifted badly out of date. Three
overlapping documents is how that happened; there is one now.

---

## The shape of the thing

```
groupwatch/
├── properties/
│   ├── index.json          generated manifest — do not hand-edit
│   ├── fma-brotherhood.json
│   ├── hickman-secret-wars.json
│   └── …                   one file per property
├── src/
│   ├── build.py            validates properties, writes the manifest
│   ├── template.html       markup, CSS, JS — the thing you edit
│   └── reading_order.py    authoring source for the Hickman order only
├── tools/                  one generator per property that needs one
├── l/                      generated — one share page per public list, see below
├── schema.sql              fresh database
├── migrate-*.sql           run once each, on an existing database
└── index.html              generated, committed, served
```

**`index.html` is generated. Don't edit it.** It is committed anyway, because
GitHub Pages has no build step of its own. The same goes for `l/`.

```
src/template.html  +  properties/index.json  →  python3 src/build.py  →  index.html + l/
```

Property *bodies* are not inlined. The page boots, reads `?p=<slug>`, and
`fetch`es that property's JSON. Only the manifest — title, kind, year, counts,
accents — is baked into the page, because the switcher needs it before first
paint.

**That means you must serve over http.** `fetch` is blocked on `file://`, so
opening the file directly gives you a page that cannot load anything. Use
`python3 -m http.server 8000`. This was already true for auth; it is now true
for the data as well.

---

## Adding a property

Drop a JSON file into `properties/` and rebuild. Nothing else.

```json
{
  "slug": "must-equal-the-filename",
  "title": "Some Show",
  "subtitle": "optional, shown under the title",
  "kind": "anime",
  "year": "2019",
  "popularity": 62,
  "blurb": "One sentence for the picker.",
  "unit":  { "one": "episode", "many": "episodes" },
  "verb":  { "base": "watch", "past": "watched", "ing": "watching" },
  "accent": "#B0472E",
  "accentDark": "#E8874F",
  "itemOrder": "number-first",
  "tiers": false,
  "sections": [ … ]
}
```

| Field | Effect |
|---|---|
| `slug` | the `?p=` value and the `property_id` in the database. **Never change it.** |
| `unit` | drives all copy — "42 episodes", "3 issues behind" |
| `verb` | drives the rest — "Watching with other people", "read" vs "watched" |
| `accent` / `accentDark` | one per theme; see *Accents* below |
| `itemOrder` | `number-first` renders `12  One is All, All is One`; the default renders `Fantastic Four #570` |
| `tiers` | `false` hides the tier columns entirely |
| `itemTiers` | tiers live on each row rather than the section — see *Tiers* |
| `weightUnit` | `{one,many}`; weights read as this instead of hours |
| `paceTiers` | which tiers the finish date covers, e.g. `[1, 2]` |
| `paceLabel` | what to call the tiers it leaves out, for the checkbox |
| `popularity` | **required**, 0–100; the catalogue is sorted by it, ties break on title. See [POPULARITY.md](POPULARITY.md) |
| `rules` | renders a house-rules panel |
| `notes` | footer prose. `["Heading.", "body"]` pairs, or a bare string |
| `forGroup` | per-group copy overrides, keyed by join code |
| `schedule` | dated windows — see *Pace* |

Sections take `id`, `title`, `sub`, optional `tier`, `intro`, `links`,
`start`, `open`.
Items take `id`, `t`, `n`, and optional `note`, `star`, `opt`, `url`, `w`,
`tier`.

### The ID rule

`item.id` is a stable key, and progress is stored as a list of them.

- **Reordering and moving items between sections is safe.** The ID travels with
  the item.
- **Renaming an ID silently destroys saved progress.** Everyone who ticked it
  loses the tick, with no error anywhere.

Prefix IDs with the property (`fmab-1`, `venom-ac-3`). `build.py` fails the
build on duplicates — a duplicate would make two checkboxes move together,
silently, which is the worst kind of bug.

`build.py` also fails on a slug that doesn't match its filename, a missing
`unit`, and a section id that isn't a valid HTML id.

---

## Rendering

**`build()`** runs once: all markup for sections and the strip via `innerHTML`,
plus a single delegated `change` listener rather than one per item.

**`paint()`** runs after every change and syncs everything visual — checkboxes,
strikethroughs, marks, counts, the export code, the schedule line, the group
stack. Recomputing everything is a few milliseconds and worth more than the
microseconds targeted updates would save.

All interpolated text goes through `esc()`. That matters more than it used to:
display names are supplied by other people now, not just by you.

### The strip

Marks are `flex-grow: var(--w, 1); flex-basis: 0`, so by default they divide
the width evenly at any count, and a property that declares weights gets marks
as wide as the thing takes. Tier-1 marks are drawn taller where a property has
tiers. Three-pixel transparent spacers separate sections.

`rowsFor()` splits the sections into at most eight contiguous rows with a DP
that minimises squared deviation from an even split. It partitions on **item
count, not weight** — partitioning on weight was tried and is worse, because it
produces rows of four enormous marks next to rows where everything is at the
minimum width.

### Section links

`links` is a list of `{label, url}`. One or two render inline in the header.
**Three or more collapse into a dropdown** — a single "N series" button that
opens a panel — because a row of uppercase links shouts over the section title
it belongs to, and a dozen of them used to break the header outright.

This is an engine rule, not a per-property one: `LINKS_INLINE` in
`src/template.html` is the only place the threshold exists, so every property
gets the behaviour without opting in and changing it is one edit. Anything new
inherits it. A link inside an open panel stops its click bubbling, or opening a
series would also collapse the section it sits on.

**Comic rows never carry their own link.** Links belong on the section header
and nowhere else. An item's `url` on a comic list only ever repeated the series
link already sitting above it, and having both meant two places to keep
correct. If a section contains an entry from a series its header does not link
— a Spectacular chapter inside an Amazing Spider-Man section, an Annual, a
crossover tie-in — **add the link to the header**, do not attach it to the row.

The one exception is a list where the row *is* the link and there is no series
to link instead: Kingdom Hearts has rows that are a YouTube video, an orchestra
transcript, a press kit. Stripping those would destroy the entry rather than
de-duplicate it. Nothing in a comic list qualifies.

### Cross-title chapters sit where you read them

A comic section built from a range — `rng(252, 300)` — plus a handful of
entries from other books must **splice those entries into the range at the
point they are read**, not append them after it. Appending is what a list
comprehension does by default and it is silently wrong: a Spectacular chapter
that belongs between two issues ends up fifty issues later, under a heading
that has already moved on.

`weave()` in `tools/spiderman_data.py` does this. Each placement is
`(anchor_id, entry)` and the entry lands directly after that anchor; several
sharing an anchor keep the order given. A missing anchor raises rather than
appending, so a renumbered section fails the build instead of quietly
scattering its chapters.

### Which section opens

Before you have marked anything, the property's own default — a section with
`open`, else one with `start`, else the first with links, else the first
section. After that, the furthest section you have touched, or the next
unfinished one if you have cleared it.

`open` exists because the links heuristic gets it wrong in both directions.
Amazing Spider-Man's prologue carries no links, so a newcomer landed past
*Amazing Fantasy* #15; Secret Wars depends on the heuristic, because its first
section is a tier-3 side series and the links are what land you on the tier-2
"start here" prelude instead. So the rule stayed and a property can now
override it outright.

This runs on the first `paint()`, not at boot, because at boot the session has
not resolved and no progress exists yet. A once-per-load guard stops it
fighting you when you collapse something mid-session.

### Weights

An item may carry `w`. Absent everywhere, every item weighs 1, `TOTALW ===
TOTAL`, and every figure reduces to the item count it was before — which is
what keeps the unweighted properties untouched.

Weights change three things: mark width, the pace line, and how far behind you
are. They do **not** change the counters — "14 / 31" stays an item count,
because "how much have I done" and "am I on schedule" are different
questions.

Weights are hours unless the property names its own unit. A comic run weighs in
issues, and rendering a twelve-issue bundle as `12h` would be wrong by a factor
of three, so `weightUnit` swaps the formatting in `hrs()`.

**The mark floor is computed per row, not fixed.** A weighted strip gives every
mark a minimum width so a four-minute video does not round to a third of a
pixel. That minimum is a claim on the row's total width — sixty-nine marks at
seven pixels demand 483px before gaps — so a flat value made rows that could
not shrink and dragged the whole page sideways on a phone. `indexStrip()` now
sets `--floor` per row from the width actually available, capped at 7px and at
60% of an even share, so there is always room left for the weighting to show.

### Alternate cuts

A film that exists in more than one version still gets **one row**. A second
row would either double the film's hours — you do not watch it twice — or have
to carry no weight, which mixes weighted and unweighted rows in a weighted
list. It would also fail to pair across lists, because rows pair by title and
year. So the cut lives in the row note, and the note says which version the
bar is measuring.

Which version that is defaults to the theatrical release, because that is what
the sources agree on and what "the film, 1982" means to a reader. Two kinds of
row depart from it, both deliberately:

- **The source only documents the cut.** *Legend*'s row measures the
  114-minute director's cut because that is the only released length Wikidata
  records.
- **The cut is the version worth watching, and we say so.** *Kingdom of
  Heaven* is the standing example — Nathan's ruling, 2026-08-25: the
  190-minute director's cut is the film, wherever it appears in this
  catalogue, and the bar measures it rather than the 144-minute theatrical
  release. **Any future list that carries this film follows the same rule.**

Either way the row note recommends a version in plain words, the number comes
from a figure the source already carries, and the override lives in one
visible place in the generator rather than in the data.

### Tiers

A tier normally belongs to a section. `itemTiers` moves the badge onto each
row, for lists whose sections are not tier-homogeneous — a release-order watch
list has years holding a film the whole saga turns on next to a spin-off nobody
needs, and they belong beside each other because that is the order they came
out in. An item's `tier` falls back to its section's, so nothing that omits it
changes.

### Accents

Every colour in the palette has a light and a dark value. A property therefore
carries `accent` and `accentDark`, and `applyAccent()` picks between them from
`prefers-color-scheme`, re-running when the system theme changes. Setting one
accent for both themes flattens the palette and leaves dark mode wearing the
light tone.

---

## Share pages

The site routes on the query string and serves one `index.html`, and a crawler
runs no JavaScript. Discord fetching `clubd.watch/?p=halo` reads the static
head and previews the generic site card — for every list alike. So the build
writes one small page per public list at **`l/<slug>.html`**, carrying nothing
but that list's own `og:` / `twitter:` tags and a bounce to the app:

```html
<meta http-equiv="refresh" content="0;url=/?p=halo">
<script>location.replace("/?p=halo")</script>
```

A crawler reads the tags and stops. A person lands on the file and is in the
app before they notice — the script is what makes it instant, the meta refresh
is what a browser with no script honours, and a single link in the body is
there for the one that honours neither. GitHub Pages serves a subdirectory's
`halo.html` at `/l/halo` as well — checked against the site's other
subdirectory pages, not against `l/` itself, so `curl -sI
https://clubd.watch/l/kubrick` after the first deploy is the confirmation —
and that is the URL the tags call canonical, so a crawler that re-fetches
`og:url` reads the same tags again rather than the generic ones at `/?p=halo`.

The description is the list's blurb, verbatim — the sentence under the title
on the list page, whose count `qa_lint` holds to the rows — and the header
line (`subtitle-or-kind · year · N units`) only for a list with no blurb. It
is not the header *and* the blurb: 81 blurbs open with the count the header
already states, and the header is lower-case because it sits over a title.
Discord caches a first embed for a long time, so the card says what the blurb
says and nothing more; CLU-213 may add to it. The image is the site card
until CLU-218 makes one per list.

**The build owns `l/`.** It removes the page of any list that was renamed or
removed, refuses anything in there it did not write, and asserts afterwards
that the directory holds exactly one page per public list. Commit it with
`index.html`; the CI check fails on a stale or untracked page.

**The gated list never gets one, and the build proves it** (CLU-214). Its page
would be a public, unlinked URL carrying its cover title — and unlinked files
are exactly how this repo has leaked before. The generator skips on the
`secret` flag, never by name, and the build fails — it does not sweep the file
as stale — if a page named for the gated list is ever found in `l/`, whether
before the pages are written or after. `check_embeds()` then reads the
directory back and fails the build if any page links to it (`?p=<slug>` or
`/l/<slug>`), titles itself with its slug or cover title, or carries its hint
or any piece of its ciphertext. The slug is an ordinary word, so a blurb that
merely uses it is not a hit. A share link to the gated list is the app URL,
`/?p=<slug>`, which a crawler reads as the generic card; `/l/<slug>.html`
simply never exists, and a missing path on Pages is GitHub's own 404 page —
no site content, no tags, no embed.

Nothing hands the `/l/` URL out yet: the template has no copy-link for a list
(that is CLU-142), and the friend and club links are their own cards. **When
one is added it must branch on the `secret` flag** and hand out `/?p=<slug>`
for the gated list, never `/l/<slug>` — the `/l/` form is a 404 for it, and
CLU-214 asks for the generic card. A generated (daily) list is skipped as
well, since its count is only known on the day it is read.

---

## Groups

Two tables, both keyed to `auth.users`, so membership follows the account
rather than the browser: `groups` (code, name, property, dates, shift) and
`group_members` (`group_id` + `user_id`, display name, colour index).

`localStorage` holds `gw:group:<slug>` — which of your groups is on screen,
per property — `gw:groupall:<slug>`, the experimental combined view, and
`gw:clubtile:<slug>`, whether the club tile is shut here.

### The club tile

The panel is one bar that opens. Shut, it says which club is drawing the strip,
how many people are in it and their colours; open, it holds the switcher, the
roster, the code you send people, and — behind three icons — the rename, the
schedule, and everything that is done once (your name, refresh, calendar,
leave, and the owner's member list). It is a `<details>`, the same element the
list's own sections fold with, so the keyboard and screen-reader behaviour is
the browser's rather than ours. Open is the default and shut is remembered per
property: the tile is where the club lives, so someone who only wants the list
closes it once.

The member legend moved into it. It used to sit under the stack as a wrapped
line; inside the tile it is the roster, one row per person, and it is still
`#glegend` painted by `paintStack()` — which is why it is a fixed slot in the
markup rather than a string `renderGroupPanel()` builds.

### More than one group per property

Nothing in the schema ever limited you to one: `group_members` is keyed on
(group, user) with no per-property constraint, and `groups.property_id` scopes
what `loadGroups()` returns. What was missing was a way in — the create/join
form was hidden the moment you were in a group, so a second one was
unreachable. `addingGroup` reopens it from the tile's foot, and the switcher
picks which group the strip draws. Its options carry a heading — the clubs for
this list sit under one `<optgroup>` — because universal groups are coming and
they need a second one beside it; a group and a watch club can then share a
name harmlessly, since they are never in the same section.

Renaming needs no new policy either. "creator updates group" already covers
`name`, the same policy that lets an owner move the schedule, so the rename
drawer is owner-only for the same reason the date controls are — and a member
is given no pencil at all rather than one that answers a press with a refusal.

A join code belongs to one property. Joining one from the wrong page succeeds
in the database and then shows nothing, because the panel only loads groups
whose `property_id` matches. The client compares the returned `property_id`
against `SLUG` and names the property instead of leaving a silent no-op.

### The combined view

`allGroups` stacks everyone from every group you are in on this property.
It is off by default and deliberately marked experimental.

**Deduplicate by person.** `loadMembers()` merges rosters into a `Map` keyed on
`user_id`, so someone in two of your groups is one layer. Without that,
`deepest[]` would rank a reader against their own second layer.

**Colours are per group, so they collide.** The group on screen keeps the
`color_index` values it already has; everyone else takes the next free index,
bounded by a `MCOLORS` counter so a full palette cannot spin. Toggling the view
therefore does not reshuffle a stack someone has learnt to read.

**One group still owns the dates.** `paceInfo()` reads `group`, not the union —
a finish date belongs to one group. The roster stays scoped to `group.id` as
well, since you can only remove someone from a group you own.

### The recursion trap

The obvious policy on `group_members` — "you may read rows of groups you belong
to" — has to query `group_members` to answer, which re-triggers the policy, and
Postgres errors out. Both membership tests are therefore `security definer`
functions (`is_group_member`, `is_group_owner`, `shares_group_with`) that run as
the owner and skip RLS on the inner read. Don't inline them back into policies.

### Joining without exposing the table

There is deliberately no select policy matching a group by code. If there were,
anyone could enumerate `groups` by guessing six characters. `join_group()` is a
`security definer` function that resolves the code and inserts your membership.
The only way to see a group is to already be in it.

Codes use a 32-character alphabet with `0`, `O`, `1` and `I` removed, so they
survive being read aloud, and `new_group_code()` re-rolls on collision.

### Property scoping

`shares_group_with(other, property)` takes the property as an argument and joins
through `groups`. Without that join, someone in your Fullmetal Alchemist group
could read your Secret Wars progress.

### Drawing the stack

`paintStack()` sorts members by count, then computes `deepest[]` — for each
column, the index of the furthest-back layer that still has that item ticked.

**Fill to the bottom where nothing is behind you.** A read mark stretches from
its layer's top to the bottom of the stack only where `deepest[idx] === i`.
Otherwise the readers behind still show as bands beneath it.

**Don't punch holes.** An unread mark is a short grey nub. Where a reader
*behind* has a stretched mark, a front layer's nub sits on top of it and cuts a
grey gap through their bar. `veil` suppresses it where `deepest[idx] > i`. This
was a real shipped bug; with two readers and one barely started, the whole bar
looked broken.

Your own layer reads the live `done` set through `readsOf()`, never a copy taken
at load — `done` is reassigned wholesale by reset, import and the first-sign-in
merge, so a cached reference goes stale in silence.

### Freshness

No realtime channel. Members are re-fetched every 45 seconds while the tab is
visible, on `visibilitychange`, and from the Refresh button. Your own layer
updates instantly because it reads `done` directly.

The stack rebuilds every mark for every reader on each tick. At 250 items and
four readers that is a thousand spans per click, comfortably inside a frame. A
much longer property or a large group would want redrawing only the layers whose
`deepest[]` entries changed. Don't optimise it until it hurts.

---

## Pace

Two models.

**Linear.** A group with a `target_date` gets a straight line from `start_date`,
and `expected = TOTAL × elapsed`.

**Windows.** A property can declare dated windows with cumulative targets:

```json
"schedule": { "kind": "windows", "windows": [
  { "start": "2026-07-15", "end": "2026-07-28", "through": 20, "label": "…" }
]}
```

`through` is the cumulative count due by the **end** of that window.

**Behind is measured against the last window that has closed**, not
interpolated inside the open one — you have until a window's end date, and
finishing early is meant to buy you off days. Interpolating would nag people who
are exactly on schedule. Two markers appear on the strip: a solid rule at what
is overdue, a lighter one at the current window's goal.

**The timeline need not cover everything on the page.** `paceTiers` names the
tiers a finish date paces you through; anything outside weighs nothing in the
pace maths, so the line sweeps past it for free and it carries no due date. A
checkbox under the strip widens the scope back to everything, stored per
property in `localStorage` under `gw:pace:<slug>` — it is a view preference,
and a column would have meant a migration.

A group's owner can slide the whole schedule with `schedule_shift_days`. Every
window moves together, so the pace is unchanged and only the dates differ. On a
property with no schedule, the owner sets, changes or removes a plain finish
date instead; removing it removes pace tracking with it.

---

## Storage

Three layers, in precedence order.

1. **`localStorage`**, always written first, keyed `gw:v1:<slug>`. A network
   failure never costs a tick.
2. **Supabase**, when a session exists, debounced 700ms, upserted on
   `(user_id, property_id)`.
3. **The export code**, `btoa(JSON.stringify([...done]))`, for moving progress
   without an account.

Sync failures are non-fatal by design: they surface in the status indicator and
log with a `[tracker]` prefix, and the local write already happened.

On first sign-in for a given user and property, `adopt()` takes the **union** of
local and server, pushes it, and sets a `gw:merged:<uid>:<slug>` flag. The union
is right once — you cannot unread something you never read — and wrong
repeatedly, because un-ticking on device A would be undone by device B's stale
copy.

`migrate()` walks two older key formats forward for the Hickman property:
positional integers → slug IDs → the per-property key.

### Per-club sessions (CLU-389)

A watch club can hold its own run rather than sharing your all-time one. When
one does, `done` is that club's session: it is cached locally under
`gw:club:v1:<club-id>` — deliberately **not** a `gw:v1:` key, which
`acctDump()` sweeps into `lists` — and it is written through a single
`save_progress(p_property, p_club, p_ids)` RPC that writes the session as an
exact set and **unions** it into your all-time `progress` row in the same
transaction. Furthest wins: a club tick can never lower a number you already
had, and unticking inside a club does not take it back off your all-time
record. A club starts empty, and nothing carries over into it.

`progress` is untouched by any of this, so every read that asks "what have you
ever watched" still answers byte-for-byte.

The front end detects the capability rather than being told about it: the one
`club_progress` read it needs either answers or comes back `42P01`, latched for
that page load. With the table and the function absent the site behaves exactly
as it did before the feature — same reads, same writes, same rendering — and
starts using them by itself once they exist. `scratch/qa2/clubprog_check.py`
executes both sides.

Groups are never sessions: a group spans every list and only ever reports
progress you already have. Neither is a fresh watch, which is a sealed personal
run, so the two are mutually exclusive by construction.

---

## What the security actually is

The anon key in the source is public by design. It identifies the project, not
a user, and Supabase expects it in client code.

The protection is row-level security, enforced by Postgres. `auth.uid()` comes
from the signed JWT issued at sign-in and cannot be forged without the project's
secret, which never leaves Supabase. A request can only ever touch rows the
policies allow, no matter what the client sends.

Joining a group makes your progress readable by that group, for that property.
That is what the shared strip is. Leaving ends it.

If you remove the policies while leaving RLS off, the anon key becomes a public
read-write handle on the whole database. Don't.

---

## Deploying

```bash
python3 src/build.py
git add -A && git commit -m "…" && git push
```

Pages redeploys in under a minute. **Forget the build and the manifest goes
stale**, so a new property never appears in the switcher.

`.vscode/tasks.json` has Build, Serve and Build-and-serve, reachable via
*Run Task*. Build is the default — `Cmd/Ctrl+Shift+B`.

Worth a hook if you will be at this a while:

```bash
cat > .git/hooks/pre-commit <<'EOF'
#!/bin/sh
python3 src/build.py && git add index.html build.json properties/index.json l
EOF
chmod +x .git/hooks/pre-commit
```

---

## Gotchas

**`progress.read_ids` must be `text[]`, not `int[]`.** It was `int[]` when IDs
were array positions. An old snippet gives you `400` on every write.

**Keep JSON pretty-printed.** Compact output turns every rebuild into one
enormous changed line and makes review impossible.

**Supabase's built-in mailer allows about two auth emails an hour.** Not enough
to sign in as a second person and test a group. GitHub OAuth costs no emails —
the provider needs enabling in Supabase and the callback is
`https://<project-ref>.supabase.co/auth/v1/callback`.

**Add `http://localhost:8000/**` to Authentication → URL Configuration →
Redirect URLs**, or magic links bounce to the production Site URL. Links already
sent have the destination baked in; request a new one after changing it.

**GitHub email privacy breaks account linking.** A GitHub account returning a
`users.noreply.github.com` address won't match your magic-link email, so
Supabase creates a separate user with separate progress. Copy the export code
before switching auth methods.

**Marvel only exposes the 20 most recent issues of a series**, and `?offset`,
`?limit` and `?byYear` are ignored. That is why most links are series-level.
Look series ids up rather than constructing them — the numeric id is what
resolves and the slug after it is decoration, so a guessed id lands silently on
somebody else's comic.

**`forGroup` is presentation, not secrecy.** Property files are served
publicly. It hides copy from the page, not from anyone who opens the JSON.
