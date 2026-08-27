"""Catch create-time resolution faults in a migration, mechanically.

WHY THIS EXISTS
---------------
migrate-groups.sql failed in production with

    ERROR: 42703: column p.share_with_groups does not exist

after passing three careful human/LLM audits. The bug was pure statement
ORDER: `group_may_read()` is `language sql`, and a SQL function body is parsed
and its column references resolved AT CREATE TIME — but the columns it read
were added 200 lines further down the file.

Ordering is exactly the kind of property a reader is bad at and a script is
good at, so this checks it deterministically instead.

THE ASYMMETRY THAT CAUSES THE BUG
---------------------------------
Resolved EAGERLY (can fail at create time):
    - `language sql` function bodies
    - RLS policy expressions
    - CHECK constraint expressions
    - `create trigger ... execute function f()`
    - `grant`/`revoke on function <signature>`

Deferred to RUNTIME (cannot fail at create time):
    - anything inside a `language plpgsql` body — stored as text, parsed on
      first call. This is why a missing pgcrypto in new_join_token() would
      have committed clean and only failed when someone clicked the button.

WHAT THIS DOES NOT DO
---------------------
It does not parse SQL. It matches identifiers this file itself defines
against the text of each eagerly-resolved object. That makes it good at the
one question it asks — "is anything used before it is created?" — and blind
to everything else. It is a complement to an audit, never a replacement.
"""
import pathlib
import re
import sys

SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                   else 'scratch/security/migrate-groups.sql')
lines = SRC.read_text(encoding='utf-8').split('\n')


def code(i):
    """The line, minus a trailing comment, or '' if the line IS a comment."""
    s = lines[i].strip()
    return '' if s.startswith('--') else s.split('--')[0]


# ---- what this file defines, and where ----------------------------------
defs = {}


def add(name, ln, kind):
    if name not in defs or ln < defs[name][0]:
        defs[name] = (ln, kind)


for i in range(len(lines)):
    c = code(i)
    m = re.search(r'add column if not exists (\w+)', c)
    if m:
        add(m.group(1), i + 1, 'column')
    m = re.search(r'create table if not exists (?:public\.)?(\w+)', c)
    if m:
        add(m.group(1), i + 1, 'table')
    m = re.search(r'create or replace function (?:public\.)?(\w+)', c)
    if m:
        add(m.group(1), i + 1, 'function')

# ---- the eagerly-resolved objects, and their text ------------------------
objs = []


def gather(start, stop_pat, label):
    """Collect code lines from `start` until stop_pat matches."""
    body, j = [], start
    while j < len(lines):
        body.append(code(j))
        if re.search(stop_pat, code(j)):
            break
        j += 1
    return '\n'.join(body), label


i = 0
while i < len(lines):
    c = code(i)

    # a function: eager only if `language sql`. Find the language on the
    # header line or the two after it.
    m = re.match(r'create or replace function (?:public\.)?(\w+)', c)
    if m:
        head = ' '.join(code(k) for k in range(i, min(i + 4, len(lines))))
        if re.search(r'\blanguage sql\b', head):
            body, _ = gather(i, r'^\s*\$\$;', 'x')
            objs.append((i + 1, 'language sql fn %s()' % m.group(1), body))
        i += 1
        continue

    if re.match(r'create policy', c):
        body, _ = gather(i, r'\);\s*$', 'x')
        objs.append((i + 1, 'RLS policy', body))
    elif 'add constraint' in c and 'check' in ' '.join(
            code(k) for k in range(i, min(i + 4, len(lines)))):
        body, _ = gather(i, r'\)\);\s*$|\);\s*$', 'x')
        objs.append((i + 1, 'CHECK constraint', body))
    elif re.match(r'create trigger', c):
        body, _ = gather(i, r';\s*$', 'x')
        objs.append((i + 1, 'trigger', body))
    elif re.match(r'(revoke|grant)\b', c) and 'on function' in c:
        body, _ = gather(i, r';\s*$', 'x')
        objs.append((i + 1, 'function grant', body))
    i += 1

# ---- the check ----------------------------------------------------------
faults, edges = [], []
for ln, label, body in objs:
    for name, (dln, kind) in defs.items():
        # word-boundary match, and never count the object's own header line
        rest = '\n'.join(body.split('\n')[1:]) if kind == 'function' else body
        if not re.search(r'\b%s\b' % re.escape(name), rest):
            continue
        if dln >= ln:
            faults.append((ln, label, name, kind, dln))
        else:
            edges.append((dln, kind, name, ln, label))

print('%s' % SRC)
print('  definitions found : %d (%d columns, %d tables, %d functions)' % (
    len(defs),
    sum(1 for v in defs.values() if v[1] == 'column'),
    sum(1 for v in defs.values() if v[1] == 'table'),
    sum(1 for v in defs.values() if v[1] == 'function')))
print('  eager objects     : %d' % len(objs))
for ln, label, _ in objs:
    print('      line %-5d %s' % (ln, label))
print('  create-time edges : %d' % len(edges))
for dln, kind, name, ln, label in sorted(edges):
    print('      %-28s (%s, line %d)  ->  %s line %d'
          % (name, kind, dln, label, ln))

if faults:
    print('\n  *** %d USE-BEFORE-DEFINE ***' % len(faults))
    for ln, label, name, kind, dln in faults:
        print('      %s at line %d uses %s %r defined at line %d'
              % (label, ln, kind, name, dln))
    print('\nVERDICT: WILL FAIL AT CREATE TIME')
    sys.exit(1)

print('\nVERDICT: clean — every eagerly-resolved reference is defined earlier')
