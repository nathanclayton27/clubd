"""Refuse to let working material under scratch/ become a public URL.

`scratch/` is gitignored, and DEPLOY.md said flatly that the site "does not
publish anything from scratch/". That sentence was false. Two QA harnesses had
been tracked at some point, and because Pages serves every tracked file,
`clubd.watch/scratch/qa2/privacy_check.py` answered 200 with the whole privacy
model written out in assertions — a map of what the site protects and how to
probe it, published.

A .gitignore does nothing once a file is tracked, so the only durable guard is a
check that runs. This is it, and CI runs it on every push (check.yml).

What stays tracked on purpose: the per-property harvest scripts and their cached
sources (`scratch/<property>/collect.py`, `*.wiki`, `*.json`). Those are how a
clone re-runs `tools/make_<property>.py` and gets the same list back, so they are
build inputs, not working material. What must never be tracked is anything in the
directories below, plus a few extensions that only ever hold notes or secrets.

    python tools/notracked.py
    python tools/notracked.py --qa

Exit 0 and silence means clean. Exit 1 lists what to untrack and how.

## --qa: the QA accounts' credentials (CLU-521)

The two QA accounts are real rows in production, and their addresses, user ids
and passwords live in one gitignored file, `scratch/qa2/accounts.env`. That file
is already refused twice over if it is ever tracked (its directory and its
extension), but a VALUE copied out of it — into a check, a note, a commit
message — would sail past both rules. This mode reads the values and refuses any
tracked file anywhere in the repo, and any commit message or author address on
HEAD or main, that contains one.

CI cannot run this half: the file is gitignored, so a runner never has it, and a
gate whose verdict depends on files git does not carry is not a gate (206a222).
So CI knows only the path rules above, and this mode is run by hand before any
commit that touches QA work. It never prints a value — only key names, paths and
commit ids.

Exit status with --qa:
    0   clean, and every key in the file was set and searched for
    2   no hit, but incomplete: the file is absent, or some keys are unset (the
        gendrift/idsafe convention — nothing wrong was found, not everything
        was looked for)
    1   a hit, or a file this mode cannot trust (an unknown key, a value too
        short to search for)
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Directories under scratch/ whose whole purpose is material that must not be
# public: test harnesses that read out the security model, SQL and audit notes,
# Linear tooling that sits next to a .env, and board snapshots naming real users.
FORBIDDEN_DIRS = (
    "scratch/qa2/",
    "scratch/security/",
    "scratch/linear/",
    "scratch/audit/",
    "scratch/audit2/",
    "scratch/audit3/",
)

# Extensions that under scratch/ only ever hold prose, secrets or migrations.
FORBIDDEN_EXTS = (".env", ".md", ".sql", ".txt", ".key", ".pem")

# Any of these appearing in a tracked file is a credential, wherever it lives.
SECRET_MARKERS = ("service_role", "SUPABASE_SERVICE", "LINEAR_API_KEY", "-----BEGIN")

# --qa. Every key in accounts.env must end in one of these. The first three are
# searched for; a username is shown to anyone the account is connected to, so it
# is not a secret, and it is short enough that searching for it would only cry
# wolf. An unknown key is refused rather than skipped: `QA_A_PASS=` would
# otherwise be a password this guard silently never looked for.
QA_ENV = ROOT / "scratch" / "qa2" / "accounts.env"
QA_GUARDED = ("_EMAIL", "_PASSWORD", "_ID")
QA_PUBLIC = ("_USERNAME",)
# Shorter than this and a value matches by accident somewhere in 40 MB of lists.
QA_MIN = 8


def tracked(prefix=None):
    args = ["git", "ls-files", "-z"] + ([prefix] if prefix else [])
    out = subprocess.run(args, cwd=ROOT, capture_output=True, check=True).stdout
    return [p.decode("utf-8", "replace") for p in out.split(b"\0") if p]


def scratch_check():
    bad = []
    for f in tracked("scratch/"):
        low = f.lower()
        if any(low.startswith(d) for d in FORBIDDEN_DIRS):
            bad.append((f, "lives in a directory that must never be tracked"))
            continue
        if any(low.endswith(e) for e in FORBIDDEN_EXTS):
            bad.append((f, "notes, secrets or SQL — never published"))
            continue
        p = ROOT / f
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in SECRET_MARKERS:
            if m in body:
                bad.append((f, "contains a credential marker (%s)" % m))
                break
    return bad


def report_scratch(bad):
    print("%d tracked file(s) under scratch/ would be served at clubd.watch:" % len(bad))
    for f, why in bad:
        print("  %-60s %s" % (f, why))
    print()
    print("Untrack them by name, keeping them on disk:")
    print("  git rm --cached " + " ".join(f for f, _ in bad))
    print()
    print("Then check the live site 404s them before you call it fixed.")


def qa_values():
    """(needles, unset, problems). A needle is (label, bytes, case_blind).

    Labels are key names and nothing else; a value never leaves this function
    except as bytes to search for.
    """
    needles, unset, problems = [], [], []
    for n, raw in enumerate(QA_ENV.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            problems.append("line %d is not KEY=VALUE" % n)
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "'\"":
            val = val[1:-1]
        up = key.upper()
        if up.endswith(QA_PUBLIC):
            continue
        if not up.endswith(QA_GUARDED):
            problems.append("%s is a key this guard does not know; name it "
                            "*_EMAIL, *_PASSWORD, *_ID or *_USERNAME" % key)
            continue
        if not val:
            unset.append(key)
            continue
        if len(val) < QA_MIN:
            problems.append("%s is under %d characters, too short to search "
                            "for without false hits" % (key, QA_MIN))
            continue
        if up.endswith("_PASSWORD"):
            needles.append((key, val.encode("utf-8"), False))
            continue
        # addresses and ids compare case-blind: neither changes meaning with case
        needles.append((key, val.lower().encode("utf-8"), True))
        if up.endswith("_EMAIL") and "@" in val:
            # the local part on its own is the shape mirrorProfile() would have
            # written into profiles.username, and the shape a note would quote
            local = val.split("@", 1)[0]
            if len(local) >= QA_MIN:
                needles.append((key + " (local part)",
                                local.lower().encode("utf-8"), True))
    return needles, unset, problems


def hits_in(blob, needles):
    low = None
    found = []
    for label, val, blind in needles:
        if blind:
            if low is None:
                low = blob.lower()
            if val in low:
                found.append(label)
        elif val in blob:
            found.append(label)
    return found


def commit_texts():
    """(sha, text) for every commit on HEAD and on main: message plus both
    addresses, so a QA address used as an identity is caught too."""
    refs = [r for r in ("HEAD", "main") if subprocess.run(
        ["git", "rev-parse", "--verify", "-q", r + "^{commit}"], cwd=ROOT,
        capture_output=True).returncode == 0]
    if not refs:
        return                          # a repository with no commits yet
    out = subprocess.run(
        ["git", "log", "--format=%H%x00%ae%x00%ce%x00%B%x1e"] + refs,
        cwd=ROOT, capture_output=True, check=True).stdout
    for rec in out.split(b"\x1e"):
        rec = rec.strip(b"\n")
        if rec:
            sha, rest = rec.split(b"\0", 1)
            yield sha.decode("ascii")[:12], rest


def qa_check():
    """Returns an exit status, and prints why for anything but a clean 0."""
    rel = QA_ENV.relative_to(ROOT).as_posix()
    if not QA_ENV.exists():
        print("WARNING: %s is absent, so --qa had nothing to search for. "
              "Nothing was checked beyond the path rules." % rel)
        return 2
    needles, unset, problems = qa_values()
    if problems:
        print("%s cannot be trusted as written, so nothing was searched:" % rel)
        for p in problems:
            print("  " + p)
        return 1

    hits = []
    for f in tracked():
        try:
            blob = (ROOT / f).read_bytes()
        except OSError:
            continue                    # deleted in the working tree
        for label in hits_in(blob, needles):
            hits.append(("file", f, label))
    for sha, text in commit_texts():
        for label in hits_in(text, needles):
            hits.append(("commit", sha, label))

    if hits:
        print("%d place(s) in the repo hold a QA account credential from %s:"
              % (len(hits), rel))
        for kind, where, label in hits:
            print("  %-6s %-50s %s" % (kind, where, label))
        print()
        kinds = {k for k, _, _ in hits}
        if "file" in kinds:
            print("A tracked file: take the value out and commit that, and if "
                  "the file was ever pushed, treat the value as public.")
        if "commit" in kinds:
            print("A commit: history cannot be quietly rewritten on main. "
                  "Rotate the credential (new password, or a new account).")
        return 1
    if unset:
        print("WARNING: no QA credential found in the repo, but %s has unset "
              "keys that were not searched for: %s" % (rel, ", ".join(unset)))
        return 2
    print("notracked --qa: %d value(s) from %s, searched in every tracked file "
          "and every commit on HEAD and main: none found."
          % (len(needles), rel))
    return 0


def main(argv):
    qa = "--qa" in argv
    unknown = [a for a in argv if a != "--qa"]
    if unknown:
        print("usage: python tools/notracked.py [--qa]")
        return 1

    bad = scratch_check()
    if bad:
        report_scratch(bad)
    rc = 1 if bad else 0
    if qa:
        if bad:
            print()
        q = qa_check()
        rc = 1 if (rc == 1 or q == 1) else q
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
